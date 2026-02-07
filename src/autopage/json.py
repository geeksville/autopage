"""Generate StreamController page JSON from autopage definitions.

Converts the high-level AutopageDef model into the JSON format expected by
StreamController's AddPage DBus API (matching the structure in doc/sample-page.json).
"""

from __future__ import annotations

import json
from typing import Any

from autopage.toml import Action, AutopageDef, Button

# ── Evdev key-code tables (from linux/input-event-codes.h) ──────────

_KEY_LEFTCTRL = 29
_KEY_LEFTSHIFT = 42
_KEY_LEFTALT = 56

# Lowercase letter → evdev keycode (keys are NOT alphabetically sequential)
_LETTER_CODES: dict[str, int] = {
    "a": 30, "b": 48, "c": 46, "d": 32, "e": 18, "f": 33, "g": 34,
    "h": 35, "i": 23, "j": 36, "k": 37, "l": 38, "m": 50, "n": 49,
    "o": 24, "p": 25, "q": 16, "r": 19, "s": 31, "t": 20, "u": 22,
    "v": 47, "w": 17, "x": 45, "y": 21, "z": 44,
}

# Digit row
_DIGIT_CODES: dict[str, int] = {
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
    "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
}

# Punctuation (unshifted)
_PUNCT_CODES: dict[str, int] = {
    "-": 12, "=": 13, "[": 26, "]": 27, ";": 39,
    "'": 40, "`": 41, "\\": 43, ",": 51, ".": 52, "/": 53,
}

# Shifted punctuation (same physical key, but needs Shift held)
_SHIFTED_PUNCT: dict[str, int] = {
    "!": 2, "@": 3, "#": 4, "$": 5, "%": 6,
    "^": 7, "&": 8, "*": 9, "(": 10, ")": 11,
    "_": 12, "+": 13, "{": 26, "}": 27, ":": 39,
    '"': 40, "~": 41, "|": 43, "<": 51, ">": 52, "?": 53,
}

# Build unified char → (keycode, needs_shift) map
_CHAR_TO_KEY: dict[str, tuple[int, bool]] = {}

for _ch, _code in _LETTER_CODES.items():
    _CHAR_TO_KEY[_ch] = (_code, False)
    _CHAR_TO_KEY[_ch.upper()] = (_code, True)

for _ch, _code in _DIGIT_CODES.items():
    _CHAR_TO_KEY[_ch] = (_code, False)

for _ch, _code in _PUNCT_CODES.items():
    _CHAR_TO_KEY[_ch] = (_code, False)

for _ch, _code in _SHIFTED_PUNCT.items():
    _CHAR_TO_KEY[_ch] = (_code, True)

# Named keys for hotkey combos and the SPACE token
_NAMED_KEYS: dict[str, int] = {
    # Modifiers
    "Ctrl": _KEY_LEFTCTRL, "Control": _KEY_LEFTCTRL,
    "Shift": _KEY_LEFTSHIFT,
    "Alt": _KEY_LEFTALT,
    # Whitespace / editing
    "SPACE": 57, "Space": 57,
    "Enter": 28, "Return": 28,
    "Tab": 15,
    "Backspace": 14,
    # Navigation
    "Escape": 1, "Esc": 1,
    "Delete": 111, "Del": 111,
    "Insert": 110, "Ins": 110,
    "Home": 102, "End": 107,
    "PageUp": 104, "PgUp": 104,
    "PageDown": 109, "PgDn": 109,
    "Up": 103, "Down": 108, "Left": 105, "Right": 106,
    # Function keys
    "F1": 59, "F2": 60, "F3": 61, "F4": 62, "F5": 63, "F6": 64,
    "F7": 65, "F8": 66, "F9": 67, "F10": 68, "F11": 87, "F12": 88,
    # Desktop
    "Super": 125, "Meta": 125,
    "CapsLock": 58, "PrintScreen": 99, "ScrollLock": 70, "Pause": 119,
}

# Also allow bare single-letter key names in combos (e.g. "Ctrl+C")
for _ch, _code in _LETTER_CODES.items():
    _NAMED_KEYS.setdefault(_ch.upper(), _code)
    _NAMED_KEYS.setdefault(_ch, _code)

# Allow digit names in combos (e.g. "Ctrl+1")
for _ch, _code in _DIGIT_CODES.items():
    _NAMED_KEYS.setdefault(_ch, _code)


def _resolve_key_name(name: str) -> int:
    """Resolve a symbolic key name to its evdev keycode."""
    if name in _NAMED_KEYS:
        return _NAMED_KEYS[name]
    raise ValueError(f"Unknown key name: {name!r}")


# ── Type-string → key events ────────────────────────────────────────


def type_string_to_keys(type_str: str) -> list[list[int]]:
    """Convert a *type* shorthand string to a list of ``[keycode, state]`` pairs.

    The string is split on spaces.  Each token is handled as:

    * ``"SPACE"`` → press/release the space bar
    * ``"Ctrl+C"`` → press modifiers, press+release final key, release modifiers
    * anything else → type each character literally (auto-shifting uppercase)

    Returns a list like ``[[29, 1], [46, 1], [46, 0], [29, 0]]``.
    """
    keys: list[list[int]] = []

    for token in type_str.split():
        if token == "SPACE":
            keys.append([57, 1])
            keys.append([57, 0])
        elif "+" in token:
            # Hotkey combo: "Ctrl+Shift+T" → split on "+"
            parts = token.split("+")
            modifiers = parts[:-1]
            final = parts[-1]

            mod_codes = [_resolve_key_name(m) for m in modifiers]
            final_code = _resolve_key_name(final)

            for mc in mod_codes:
                keys.append([mc, 1])
            keys.append([final_code, 1])
            keys.append([final_code, 0])
            for mc in reversed(mod_codes):
                keys.append([mc, 0])
        else:
            # Literal characters
            for ch in token:
                if ch not in _CHAR_TO_KEY:
                    raise ValueError(f"Cannot type character: {ch!r}")
                keycode, needs_shift = _CHAR_TO_KEY[ch]
                if needs_shift:
                    keys.append([_KEY_LEFTSHIFT, 1])
                keys.append([keycode, 1])
                keys.append([keycode, 0])
                if needs_shift:
                    keys.append([_KEY_LEFTSHIFT, 0])

    return keys


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
        state["media"] = {"path": button.icon, "size": 0.84}

    return {"states": {"0": state}}


def generate_page_json(
    definition: AutopageDef,
    *,
    grid_rows: int = 4,
    grid_cols: int = 4,
) -> dict[str, Any]:
    """Build a full StreamController page JSON dict from an *AutopageDef*.

    Buttons with an explicit ``location`` are placed there; others are
    auto-placed in row-major order into the first available cell.
    """
    page: dict[str, Any] = {
        "settings": {
            "auto-change": {"enable": True, "stay-on-page": False},
            "background": {"overwrite": True, "show": True},
        },
        "keys": {},
    }

    occupied: set[str] = set()

    # Reserve explicitly placed locations first
    for button in definition.buttons:
        if button.location:
            occupied.add(button.location)

    def _next_location() -> str:
        for r in range(grid_rows):
            for c in range(grid_cols):
                loc = f"{r}x{c}"
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
