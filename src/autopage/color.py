"""Shared color-parsing utilities used by both backends.

Both the StreamController JSON backend and the touchy-pad backend need to
parse HTML5 colour strings, but they consume the result differently:

* StreamController JSON needs ``[R, G, B, A]`` (alpha encodes opacity).
* touchy-pad / LVGL uses ``0xRRGGBB`` integers; the Style proto has no
  ``bg_opa`` field, so opacity is baked into the colour by blending with
  black.
"""

from __future__ import annotations

import webcolors

# Default opacity applied to button backgrounds when not specified.
DEFAULT_OPACITY = 0.75


def parse_color_rgba(color_str: str, opacity: float = DEFAULT_OPACITY) -> list[int]:
    """Parse an HTML5 colour string into ``[R, G, B, A]``.

    Uses :func:`webcolors.html5_parse_legacy_color` so any valid HTML5 colour
    is accepted (named colours like ``"green"``, hex like ``"#ff2244"``, etc.).

    *opacity* (0.0–1.0) is converted to the alpha byte (0–255).
    """
    c = webcolors.html5_parse_legacy_color(color_str)
    alpha = max(0, min(255, round(opacity * 255)))
    return [c.red, c.green, c.blue, alpha]


def parse_color_int(color_str: str, opacity: float = DEFAULT_OPACITY) -> int:
    """Parse an HTML5 colour string into a packed ``0xRRGGBB`` integer.

    Because the touchy-pad Style proto has no ``bg_opa`` field, *opacity* is
    applied by blending each channel with black (i.e. multiplying by
    *opacity*).  This matches the visual result you would get on a black
    background — a 0.75-opacity blue looks like a slightly dimmed blue.
    """
    c = webcolors.html5_parse_legacy_color(color_str)
    r = max(0, min(255, round(c.red * opacity)))
    g = max(0, min(255, round(c.green * opacity)))
    b = max(0, min(255, round(c.blue * opacity)))
    return (r << 16) | (g << 8) | b
