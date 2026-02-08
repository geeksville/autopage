"""Evdev keycode mappings and type-string to key-event conversion."""

from __future__ import annotations

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
    "Delete": 111,
    "Insert": 110,
    "Home": 102, "End": 107,
    "PageUp": 104,
    "PageDown": 109,
    "Up": 103, "Down": 108, "Left": 105, "Right": 106,
    # Function keys
    "F1": 59, "F2": 60, "F3": 61, "F4": 62, "F5": 63, "F6": 64,
    "F7": 65, "F8": 66, "F9": 67, "F10": 68, "F11": 87, "F12": 88,
    "F13": 183, "F14": 184, "F15": 185, "F16": 186, "F17": 187, "F18": 188,
    "F19": 189, "F20": 190, "F21": 191, "F22": 192, "F23": 193, "F24": 194,
    # Desktop
    "Super": 125, "Meta": 125,
    "CapsLock": 58, "PrintScreen": 99, "ScrollLock": 70, "Pause": 119,
    # Clipboard operations
    "Copy": 133, "Paste": 135, "Cut": 137,
    # Media keys
    "Mute": 113,
    "VolumeDown": 114, "VolumeUp": 115,
    "Play": 164,
    "Stop": 166,
    "Previous": 165,
    "Next": 163,
    # Punctuation keys useful in combos
    "`": 41, "Grave": 41,
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
        elif "+" in token and token != "+":
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
