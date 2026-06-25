"""Fetch a page background image over HTTP for the touchy-pad backend.

Deliberately does no image processing: :class:`touchy_pad.api.image_cache.ImageCache`
already normalises whatever bytes we hand it (GIF passthrough so animation is
preserved, static images converted to LVGL ``.bin``, aspect-preserving downscale
to its ``max_dim``). So this module only knows how to fetch a URL and return the
raw bytes — a missing or broken background degrades to "no background" and never
breaks page rendering.
"""

from __future__ import annotations

import logging
import urllib.request

log = logging.getLogger(__name__)

# Matches the `touchpad_image` CLI: a browser User-Agent (Cloudflare blocks the
# default python UA) and a generous timeout.
_USER_AGENT = "Mozilla/5.0 (compatible; touchy-pad/1.0)"
_FETCH_TIMEOUT_S = 30


def fetch_background(url: str) -> bytes | None:
    """Fetch *url* and return its raw bytes, or ``None`` on any error.

    Only ``http``/``https`` URLs are fetched; anything else (or a network /
    decode failure) logs a warning and returns ``None`` so the caller renders
    the page with no background.
    """
    if not url.lower().startswith(("http://", "https://")):
        log.warning("Ignoring non-http(s) background url %r", url)
        return None

    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT_S) as resp:  # noqa: S310
            data = resp.read()
    except Exception as exc:  # noqa: BLE001 — any fetch failure → no background.
        log.warning("Failed to fetch background %r: %s", url, exc)
        return None

    log.info("Fetched background %r (%d bytes)", url, len(data))
    return data


__all__ = ["fetch_background"]
