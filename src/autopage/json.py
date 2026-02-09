"""Generate StreamController page JSON from autopage definitions.

Converts the high-level AutopageDef model into the JSON format expected by
StreamController's AddPage DBus API (matching the structure in doc/sample-page.json).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from autopage.keys import type_string_to_keys
from autopage.toml import Action, AutopageDef, Button

import webcolors

log = logging.getLogger(__name__)

# Default opacity applied to button backgrounds when not specified.
DEFAULT_OPACITY = 0.75


# ── Color parsing ────────────────────────────────────────────────────


def _parse_color(color_str: str, opacity: float = DEFAULT_OPACITY) -> list[int]:
    """Parse an HTML5 color string into ``[R, G, B, A]``.

    Uses :func:`webcolors.html5_parse_legacy_color` so any valid HTML5 color
    is accepted (named colours like ``"green"``, hex like ``"#ff2244"``, etc.).

    *opacity* (0.0 – 1.0) is converted to the alpha byte (0 – 255).
    """
    c = webcolors.html5_parse_legacy_color(color_str)
    alpha = max(0, min(255, round(opacity * 255)))
    return [c.red, c.green, c.blue, alpha]


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
        opacity = button.opacity if button.opacity is not None else DEFAULT_OPACITY
        state["background"] = {"color": _parse_color(button.background, opacity)}

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
    grid_rows: int = 3,
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
        try:
            page["keys"][location] = _button_to_json(button)
        except Exception as e:
            log.error(f"Skipping button at {location} due to: {e}")

    return page


def page_json_to_string(page: dict[str, Any]) -> str:
    """Serialize a page dict to a formatted JSON string."""
    return json.dumps(page, indent=4)
