"""Render a backend-neutral :class:`~autopage.toml.AutopageDef` into a
touchy-pad user-screen page body (a ``Widget`` grid of ``image_button``\\s).

Mirrors ``touchy_pad.touchydeck.layout.build_page`` but, instead of a blank
StreamDeck grid, each cell carries the autopage button's actions:

* ``type`` shorthand actions become device-side ``macro_action``\\s
  (see :mod:`autopage.keys_hid`);
* StreamController-only actions (explicit ``id`` + ``settings``) become a
  ``host_action`` running a host-side stub that logs the request — a hook to
  flesh out later.

Buttons with an ``icon`` get a Material Design icon image (rendered by
:mod:`autopage.touchy.icons`); the rest fall back to the shared placeholder.
"""

from __future__ import annotations

import logging

from autopage.color import DEFAULT_OPACITY, parse_color_int
from autopage.keys_hid import type_string_to_macro_steps
from autopage.toml import AutopageDef, Button
from autopage.touchy.icons import render_icon

log = logging.getLogger(__name__)

# Native StreamDeck-classic key size; matches touchydeck so the same panel
# yields the same grid.
KEY_PIXELS = 72
KEY_GAP = 4

# Fallback grid used when no device is connected (e.g. --dry-run without
# hardware) so rendering still produces a sensible layout.
DEFAULT_COLS = 5
DEFAULT_ROWS = 3


def auto_grid(display_w: int, display_h: int) -> tuple[int, int]:
    """How many native ``KEY_PIXELS`` keys fit in ``display_w x display_h``.

    Same arithmetic as ``TouchyDeck._auto_grid``: uniform gaps between cells
    and at the panel edges.
    """
    pitch = KEY_PIXELS + KEY_GAP
    cols = max(1, (max(0, display_w) - KEY_GAP) // pitch)
    rows = max(1, (max(0, display_h) - KEY_GAP) // pitch)
    return int(cols), int(rows)


def page_pixels(cols: int, rows: int) -> tuple[int, int]:
    """Pixel size of a ``cols x rows`` page body (cells + surrounding gaps)."""
    page_w = cols * KEY_PIXELS + (cols + 1) * KEY_GAP
    page_h = rows * KEY_PIXELS + (rows + 1) * KEY_GAP
    return page_w, page_h


def _parse_location(location: str) -> tuple[int, int] | None:
    """Parse a ``"<col>x<row>"`` location string into ``(col, row)``."""
    try:
        col_str, row_str = location.lower().split("x", 1)
        return int(col_str), int(row_str)
    except (ValueError, AttributeError):
        log.warning("Bad button location %r, auto-placing instead", location)
        return None


def _button_actions(button: Button):
    """Build the list of touchy ``Action``\\s for one autopage button."""
    from touchy_pad.api import host_action, macro_action

    actions = []
    for action in button.actions:
        if action.type is not None:
            steps = type_string_to_macro_steps(action.type)
            if steps:
                actions.append(macro_action(steps))
            else:
                log.warning("Action type %r produced no macro steps", action.type)
        elif action.id is not None:
            # StreamController-only plugin action — no device-side equivalent.
            # Run a host-side stub that logs so the button still does something
            # and we have a place to implement real behaviour later.
            actions.append(host_action(on_event=_make_stub(action.id, action.settings)))
        else:
            log.warning("Button action has neither type nor id, skipping")
    return actions


def _make_stub(action_id: str, settings: dict | None):
    """Return a host-event callback that logs an unimplemented action."""

    def _stub(event) -> None:
        log.info(
            "autopage: host stub for StreamController action %r (settings=%r) fired from widget %r",
            action_id,
            settings,
            getattr(event, "user_data", None),
        )

    return _stub


def render_widget(
    definition: AutopageDef,
    *,
    cols: int,
    rows: int,
    placeholder_path: str,
    background_path: str | None = None,
):
    """Build the user-screen page body ``Widget`` for *definition*.

    Buttons with an explicit ``location`` are placed there; the rest are
    auto-placed in row-major order into the first free cell (mirrors
    ``autopage.json.generate_page_json``).

    When *background_path* is given (an already-uploaded device image path),
    the grid is composited on top of a full-page background image: the image is
    drawn first and the grid second (LVGL paints siblings in child order), so
    per-button ``opacity`` lets the backdrop show through.
    """
    from touchy_pad.api import protobuf
    from touchy_pad.api import screens as s

    occupied: set[tuple[int, int]] = set()
    placements: list[tuple[Button, tuple[int, int]]] = []

    # Reserve explicitly-placed cells first.
    explicit: dict[int, tuple[int, int]] = {}
    for i, button in enumerate(definition.buttons):
        if button.location:
            cell = _parse_location(button.location)
            if cell is not None:
                explicit[i] = cell
                occupied.add(cell)

    def next_cell() -> tuple[int, int] | None:
        for r in range(rows):
            for c in range(cols):
                if (c, r) not in occupied:
                    occupied.add((c, r))
                    return (c, r)
        return None

    for i, button in enumerate(definition.buttons):
        cell = explicit.get(i)
        if cell is None:
            cell = next_cell()
        if cell is None:
            log.warning("No free grid cell for button %d, dropping", i)
            continue
        placements.append((button, cell))

    children = []
    for i, (button, (col, row)) in enumerate(placements):
        asset = placeholder_path
        if button.icon:
            png = render_icon(button.icon, size=KEY_PIXELS)
            if png is not None:
                asset = png

        bg_color = None
        if button.background:
            opacity = button.opacity if button.opacity is not None else DEFAULT_OPACITY
            bg_color = parse_color_int(button.background, opacity)
        btn_style = s.style(bg_color=bg_color, shadow_width=0, border_w=0)

        btn = s.image_button(
            id=f"ap_btn_{i}",
            asset=asset,
            on_click=_button_actions(button),
            style=btn_style,
        )
        children.append(s.cell(btn, col=col, row=row, grow_x=1, grow_y=1))

    grid = protobuf.Widget(id="autopage_root")
    grid.layout_grid.cols = cols
    grid.layout_grid.rows = rows
    grid.layout_grid.gap = KEY_GAP
    grid.layout_grid.layout.children.extend(children)

    if background_path is None:
        return grid

    # Composite the grid over a full-page background image. Both children fill
    # the page rect; the image is first (drawn underneath), the grid second.
    page_w, page_h = page_pixels(cols, rows)
    grid.id = "autopage_grid"
    grid.rect.CopyFrom(s.rect(0, 0, page_w, page_h))

    background = s.image(
        id="autopage_bg",
        asset=background_path,
        rect=s.rect(0, 0, page_w, page_h),
    )

    root = protobuf.Widget(id="autopage_root")
    root.rect.CopyFrom(s.rect(0, 0, page_w, page_h))
    root.layout_absolute.layout.children.extend([background, grid])
    return root
