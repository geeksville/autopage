"""Touchy-Pad backend for autopage.

:class:`TouchyApiClient` renders autopage definitions into touchy-pad
user-screen page bodies and uploads them directly to a connected device,
replacing the StreamController DBus round-trip. This is the default backend.
"""

from __future__ import annotations

import atexit
import logging
import time
from typing import Any

from autopage.api_client import ApiClient
from autopage.toml import AutopageDef
from autopage.touchy.render import DEFAULT_COLS, DEFAULT_ROWS, auto_grid, render_widget

log = logging.getLogger(__name__)

# How often to poll the foreground-window source in listen mode.
POLL_INTERVAL_S = 1.0

# Shared placeholder icon path. Uploaded once per connection to the volatile
# PSRAM ramdisk and referenced by every button until real icon selection lands.
PLACEHOLDER_PATH = "R:host/autopage/blank.bin"

# A minimal opaque "blank" LVGL ``.bin``: a 1x1 dark-grey RGB565 pixel stretched
# to fill the cell. Identical to ``touchy_pad.touchydeck.layout.BLANK_BIN`` so
# both render the same placeholder; inlined to avoid importing the touchydeck
# package (and its optional StreamDeck dependency).
_BLANK_BIN: bytes = bytes(
    [
        0x19,
        0x12,
        0x00,
        0x00,  # magic, cf=RGB565, flags
        0x01,
        0x00,
        0x01,
        0x00,  # w=1, h=1
        0x02,
        0x00,
        0x00,
        0x00,  # stride=2, reserved
        0x82,
        0x10,  # pixel: rgb565(0x10,0x10,0x10) little-endian
    ]
)


class TouchyApiClient(ApiClient):
    """Backend that talks directly to a touchy-pad device."""

    def __init__(self) -> None:
        self._pad = None
        self._placeholder_uploaded = False
        self._image_cache = None

    # ── Connection management ────────────────────────────────────────

    def _ensure_pad(self):
        """Open (and cache) the first connected touchy-pad device."""
        if self._pad is None:
            from touchy_pad.api import touchy_open

            self._pad = touchy_open()
            atexit.register(self._close)
        return self._pad

    def _close(self) -> None:
        if self._pad is not None:
            try:
                self._pad.close()
            except Exception:  # noqa: BLE001 — best-effort cleanup at exit.
                log.debug("Error closing touchy-pad device", exc_info=True)
            self._pad = None
            self._image_cache = None

    def _ensure_placeholder(self, pad) -> None:
        if not self._placeholder_uploaded:
            pad.file_save(PLACEHOLDER_PATH, _BLANK_BIN)
            self._placeholder_uploaded = True

    def _grid_dims(self) -> tuple[int, int]:
        """Grid dimensions from the device panel, or a default fallback."""
        try:
            pad = self._ensure_pad()
            info = pad.board_info
            if info is not None:
                return auto_grid(info.display_width, info.display_height)
        except Exception as exc:  # noqa: BLE001 — fall back when no device.
            log.warning("No touchy-pad device for layout (%s); using default grid", exc)
        return DEFAULT_COLS, DEFAULT_ROWS

    # ── ApiClient: rendering ─────────────────────────────────────────

    def render_page(self, definition: AutopageDef, *, decks: list[str] | None = None) -> Any:
        cols, rows = self._grid_dims()
        log.info("Rendering touchy page on a %dx%d grid", cols, rows)
        background_path = self._prepare_background(definition, cols, rows)
        return render_widget(
            definition,
            cols=cols,
            rows=rows,
            placeholder_path=PLACEHOLDER_PATH,
            background_path=background_path,
        )

    def _prepare_background(self, definition: AutopageDef, cols: int, rows: int) -> str | None:
        """Fetch + cache the page background, returning its device path.

        Returns ``None`` (and renders the bare grid) when no ``[background] url``
        is set, no device is connected, or the fetch fails. The image is cached
        on the device's transient ``T:`` drive, scaled aspect-preserving to the
        page size; GIFs keep animating (``ImageCache`` passes them through).
        """
        url = definition.background_url
        if not url:
            return None

        from autopage.touchy import background as _background
        from autopage.touchy.render import page_pixels

        try:
            pad = self._ensure_pad()
        except Exception as exc:  # noqa: BLE001 — no device → no background.
            log.warning("No device for background image (%s); skipping", exc)
            return None

        raw = _background.fetch_background(url)
        if raw is None:
            return None

        page_w, page_h = page_pixels(cols, rows)
        try:
            from touchy_pad.api import ImageCache

            if self._image_cache is None:
                self._image_cache = ImageCache(pad, max_dim=max(page_w, page_h))
            return self._image_cache.set_cached_image(raw)
        except Exception as exc:  # noqa: BLE001 — caching failure → no background.
            log.warning("Failed to cache background %r: %s", url, exc)
            return None

    def artifact_to_text(self, artifact: Any) -> str:
        return str(artifact)

    # ── ApiClient: delivery ──────────────────────────────────────────

    def push_page(
        self,
        page_name: str,
        artifact: Any,
        *,
        force: bool = False,
        known_pages: set[str] | None = None,
    ) -> bool:
        pad = self._ensure_pad()
        self._ensure_placeholder(pad)
        pad.user_screen_save(page_name, artifact)
        if known_pages is not None:
            known_pages.add(page_name)
        log.info("Page %r uploaded to touchy-pad", page_name)
        return True

    def get_controllers(self) -> list[str]:
        # Reuse the single shared device handle rather than re-enumerating via
        # libusb. A separate usb.core enumeration (touchy_get_pad_ids) opens its
        # own device handle to read the serial string, which on some hosts (e.g.
        # dev containers, where the device is only reachable through the
        # /host/dev/bus/usb fallback) corrupts libusb's device state so the
        # subsequent real touchy_open() fails with DeviceNotFound. We don't need
        # the serial for anything — render_page ignores the controller list — so
        # just report whether a device opened.
        try:
            self._ensure_pad()
        except Exception as exc:  # noqa: BLE001 — no device attached.
            log.warning("No touchy-pad device found: %s", exc)
            return []
        return ["touchy-pad"]

    def get_pages(self) -> list[str]:
        # Stage 1 always (re)uploads; we don't enumerate on-device user screens.
        return []

    def set_active_page(self, serial: str, name: str) -> None:
        pad = self._ensure_pad()
        pad.show_user_screen(name)

    # ── Foreground-window listener ───────────────────────────────────

    def listen_foreground(self, callback) -> None:
        """Poll the foreground window and dispatch changes to ``callback``.

        Unlike the StreamController backend (which receives a DBus signal),
        touchy-pad has no window source of its own, so we poll an OS-neutral
        :class:`~autopage.foreground.ForegroundSource` (``kdotool`` on KDE)
        once per :data:`POLL_INTERVAL_S`. ``callback(window_name,
        window_class)`` fires only when the focused window changes
        (edge-triggered), matching the SC backend's contract. Blocks until
        ``KeyboardInterrupt``.
        """
        from autopage.foreground import get_default_source

        source = get_default_source()
        log.info(
            "Polling foreground window every %.1fs (Ctrl+C to stop)…",
            POLL_INTERVAL_S,
        )

        last_key: tuple[str, str] | None = None
        try:
            while True:
                win = source.get_active_window()
                if win is not None:
                    key = (win.window_class, win.name)
                    if key != last_key:
                        last_key = key
                        try:
                            callback(win.name, win.window_class)
                        except Exception:  # noqa: BLE001 — keep listening.
                            log.exception("foreground callback raised")
                time.sleep(POLL_INTERVAL_S)
        except KeyboardInterrupt:
            log.info("Stopped foreground polling.")


__all__ = ["TouchyApiClient", "PLACEHOLDER_PATH"]
