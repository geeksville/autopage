"""Touchy-Pad backend for autopage.

:class:`TouchyApiClient` renders autopage definitions into touchy-pad
user-screen page bodies and uploads them directly to a connected device,
replacing the StreamController DBus round-trip. This is the default backend.
"""

from __future__ import annotations

import atexit
import logging
from typing import Any

from autopage.api_client import ApiClient
from autopage.toml import AutopageDef
from autopage.touchy.render import DEFAULT_COLS, DEFAULT_ROWS, auto_grid, render_widget

log = logging.getLogger(__name__)

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
        return render_widget(definition, cols=cols, rows=rows, placeholder_path=PLACEHOLDER_PATH)

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


__all__ = ["TouchyApiClient", "PLACEHOLDER_PATH"]
