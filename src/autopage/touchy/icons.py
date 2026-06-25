"""Render Material Design icon names into PNG bytes for touchy-pad buttons.

A thin wrapper around the :mod:`material_icons` (``python-material-icons``)
library. The autopage ``Button.icon`` field already carries Material Design icon
names verbatim (``content_copy``, ``home``, ``arrow_back``, …), so no name
translation beyond light normalisation is required.

The touchy ``image_button(asset=...)`` accepts raw PNG ``bytes`` directly, so the
PNG returned here can be handed straight to it; the device upload happens later
when the user screen is saved.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

# Native StreamDeck-classic key size; matches render.KEY_PIXELS so icons fill a
# cell. Kept local to avoid importing render (which imports the touchy API).
DEFAULT_ICON_SIZE = 72

# White outlined icons read well on the coloured button backgrounds.
DEFAULT_ICON_COLOR = "#ffffff"
DEFAULT_ICON_STYLE = "outlined"

_icons = None  # lazily-created material_icons.MaterialIcons singleton


def _get_icons():
    """Return a cached ``MaterialIcons`` instance, or ``None`` if unavailable."""
    global _icons
    if _icons is None:
        try:
            from material_icons import MaterialIcons

            _icons = MaterialIcons()
        except Exception:  # pragma: no cover - import/environment failure
            log.warning("python-material-icons is unavailable; using placeholder icons")
            _icons = False
    return _icons or None


def _normalise(name: str) -> str:
    """Normalise an icon name to the library's snake_case convention."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def render_icon(
    name: str,
    *,
    size: int = DEFAULT_ICON_SIZE,
    color: str = DEFAULT_ICON_COLOR,
    style: str = DEFAULT_ICON_STYLE,
) -> bytes | None:
    """Render Material Design icon *name* to PNG bytes.

    Returns ``None`` (logging a warning) when the icon is unknown or the library
    is unavailable, so callers can fall back to the placeholder image.
    """
    icons = _get_icons()
    if icons is None:
        return None

    from material_icons import IconStyle

    try:
        icon_style = IconStyle(style)
    except (ValueError, TypeError):
        icon_style = IconStyle.OUTLINED

    try:
        return icons.get(_normalise(name), size=size, color=color, style=icon_style)
    except FileNotFoundError:
        log.warning("Unknown Material Design icon %r; using placeholder", name)
        return None
    except Exception:  # pragma: no cover - unexpected render failure
        log.warning("Failed to render Material Design icon %r; using placeholder", name)
        return None
