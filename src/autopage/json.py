"""Generate StreamController page JSON from autopage definitions.

Converts the high-level AutopageDef model into the JSON format expected by
StreamController's AddPage DBus API (matching the structure in doc/sample-page.json).
"""

from __future__ import annotations

import json
from typing import Any

from autopage.keys import type_string_to_keys
from autopage.toml import Action, AutopageDef, Button


# ── Color parsing ────────────────────────────────────────────────────


def _parse_rgba_hex(color_str: str) -> list[int]:
    """Parse RGB or RGBA hex color strings into ``[R, G, B, A]``.

    Accepts formats: ``'0xRRGGBB'``, ``'0xRRGGBBAA'``, ``'#RRGGBB'``, ``'#RRGGBBAA'``.
    If only RGB is provided (6 hex digits), alpha defaults to 255 (0xFF).
    """
    s = color_str.removeprefix("0x").removeprefix("0X").removeprefix("#")
    if len(s) == 6:
        # RGB format - default alpha to 255
        return [int(s[i : i + 2], 16) for i in (0, 2, 4)] + [255]
    elif len(s) == 8:
        # RGBA format
        return [int(s[i : i + 2], 16) for i in (0, 2, 4, 6)]
    else:
        raise ValueError(f"Expected 6 or 8 hex digits for RGB/RGBA color, got: {color_str!r}")


# ── JSON generation ─────────────────────────────────────────────────


def _action_to_json(action: Action) -> dict[str, Any]:
    """Convert an Action to a StreamController JSON action dict."""
    if action.type is not None:
        return {
            "id": "com_core447_OSPlugin::Hotkey",
            "settings": {"keys": type_string_to_keys(action.type)},
        }
    if action.id is not None:
        return {
            "id": action.id,
            "settings": action.settings or {},
        }
    return {"id": "", "settings": {}}


def _button_to_json(button: Button) -> dict[str, Any]:
    """Convert a Button to a StreamController JSON key entry."""
    state: dict[str, Any] = {
        "actions": [_action_to_json(a) for a in button.actions],
        # "image-control-action": 0,
        # "label-control-actions": [0, 0, 0],
        # "background-control-action": 0,
    }

    # Labels
    labels: dict[str, Any] = {}
    if button.top:
        labels["top"] = {"text": button.top}
    if button.center:
        labels["center"] = {"text": button.center}
    if button.bottom:
        labels["bottom"] = {"text": button.bottom}
    if labels:
        state["labels"] = labels

    # Background colour
    if button.background:
        state["background"] = {"color": _parse_rgba_hex(button.background)}

    # Icon → media path hint (the runtime will resolve it against icon packs)
    if button.icon:
        m: dict[str, str | float] = {"path": button.icon }
        if button.size is not None:
            m["size"] = button.size
        state["media"] = m

    return {"states": {"0": state}}


def generate_page_json(
    definition: AutopageDef,
    *,
    decks: list[str] | None = None,
    grid_rows: int = 4,
    grid_cols: int = 5,
) -> dict[str, Any]:
    """Build a full StreamController page JSON dict from an *AutopageDef*.

    Buttons with an explicit ``location`` are placed there; others are
    auto-placed in row-major order into the first available cell.
    """
    page: dict[str, Any] = {
        "settings": {},
        "keys": {},
    }

    # Emit auto-change settings when match rules are defined
    if definition.matches:
        auto_change: dict[str, Any] = {
            "enable": True,
            "stay-on-page": False,
        }
        if decks:
            auto_change["decks"] = decks
        for match in definition.matches:
            if match.class_pattern:
                auto_change["wm-class"] = match.class_pattern
            if match.name_pattern:
                auto_change["title"] = match.name_pattern
        page["settings"]["auto-change"] = auto_change

    occupied: set[str] = set()

    # Reserve explicitly placed locations first
    for button in definition.buttons:
        if button.location:
            occupied.add(button.location)

    def _next_location() -> str:
        for r in range(grid_rows):
            for c in range(grid_cols):
                loc = f"{c}x{r}"
                if loc not in occupied:
                    occupied.add(loc)
                    return loc
        raise RuntimeError("No more grid positions available")

    for button in definition.buttons:
        location = button.location or _next_location()
        page["keys"][location] = _button_to_json(button)

    return page


def page_json_to_string(page: dict[str, Any]) -> str:
    """Serialize a page dict to a formatted JSON string."""
    return json.dumps(page, indent=4)
