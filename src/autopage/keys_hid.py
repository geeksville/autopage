"""Translate autopage *type* shorthand strings into touchy-pad HID macro steps.

autopage's :mod:`autopage.keys` emits **evdev** keycodes for StreamController.
touchy-pad macros instead use **HID usage IDs** (page 0x07) plus a modifier
bitmask. This module mirrors :func:`autopage.keys.type_string_to_keys` but emits
a list of ``touchy_pad`` ``MacroStep`` protobufs ready for ``macro_action``.

The character / named-key tables are sourced from
``touchy_pad.api.hid_keys`` so the HID numbering stays authoritative.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def _named_keys() -> dict[str, int]:
    """Map symbolic key names to HID keycodes (non-modifier keys only)."""
    from touchy_pad.api import hid_keys as k

    named: dict[str, int] = {
        "Space": k.KEY_SPACE,
        "Enter": k.KEY_ENTER,
        "Return": k.KEY_ENTER,
        "Tab": k.KEY_TAB,
        "Backspace": k.KEY_BACKSPACE,
        "Escape": k.KEY_ESC,
        "Esc": k.KEY_ESC,
        "Delete": k.KEY_DELETE,
        "Insert": k.KEY_INSERT,
        "Home": k.KEY_HOME,
        "End": k.KEY_END,
        "PageUp": k.KEY_PAGEUP,
        "PageDown": k.KEY_PAGEDOWN,
        "Up": k.KEY_UP,
        "Down": k.KEY_DOWN,
        "Left": k.KEY_LEFT,
        "Right": k.KEY_RIGHT,
        "CapsLock": k.KEY_CAPSLOCK,
        "Grave": k.KEY_GRAVE,
        "`": k.KEY_GRAVE,
        "Minus": k.KEY_MINUS,
        "Plus": k.KEY_EQUAL,
    }
    for n in range(1, 13):
        named[f"F{n}"] = getattr(k, f"KEY_F{n}")
    # Bare single letters / digits used inside combos (e.g. "Ctrl+C").
    for ch in "abcdefghijklmnopqrstuvwxyz":
        code = getattr(k, f"KEY_{ch.upper()}")
        named.setdefault(ch, code)
        named.setdefault(ch.upper(), code)
    for digit in "0123456789":
        named.setdefault(digit, getattr(k, f"KEY_{digit}"))
    return named


def _modifier_mask(name: str) -> int | None:
    """Return the HID modifier bit for *name*, or None if not a modifier."""
    from touchy_pad.api import hid_keys as k

    return {
        "Ctrl": k.MOD_LCTRL,
        "Control": k.MOD_LCTRL,
        "Shift": k.MOD_LSHIFT,
        "Alt": k.MOD_LALT,
        "Super": k.MOD_LGUI,
        "Meta": k.MOD_LGUI,
        "Gui": k.MOD_LGUI,
    }.get(name)


def type_string_to_macro_steps(type_str: str):
    """Convert a *type* shorthand string to a list of touchy ``MacroStep``.

    Tokens are space-separated and handled like
    :func:`autopage.keys.type_string_to_keys`:

    * ``"SPACE"`` → tap the space bar
    * ``"+Enter"`` → tap a single named key
    * ``"Ctrl+Shift+T"`` → tap the final key with the modifier bitmask
    * anything else → type each character literally (auto-shifting)

    Unknown named keys are skipped with a warning (e.g. clipboard names that
    have no HID usage-page-0x07 code).
    """
    from touchy_pad.api import hid_keys, macros

    named = _named_keys()
    steps = []

    def tap_named(name: str) -> None:
        code = named.get(name)
        if code is None:
            log.warning("No HID keycode for named key %r, skipping", name)
            return
        steps.append(macros.key_tap(code))

    for token in type_str.split():
        if token == "SPACE":
            steps.append(macros.key_tap(hid_keys.KEY_SPACE))
        elif token.startswith("+") and len(token) > 1:
            tap_named(token[1:])
        elif "+" in token and token != "+":
            parts = token.split("+")
            modifiers, final = parts[:-1], parts[-1]
            mask = 0
            ok = True
            for mod in modifiers:
                bit = _modifier_mask(mod)
                if bit is None:
                    log.warning("Unknown modifier %r in %r, skipping token", mod, token)
                    ok = False
                    break
                mask |= bit
            if not ok:
                continue
            final_code = named.get(final)
            if final_code is None:
                log.warning("No HID keycode for %r in combo %r, skipping", final, token)
                continue
            steps.append(macros.key_tap(final_code, modifiers=mask))
        else:
            for ch in token:
                mapping = hid_keys.char_to_key(ch)
                if mapping is None:
                    log.warning("Cannot type character %r, skipping", ch)
                    continue
                code, mods = mapping
                steps.append(macros.key_tap(code, modifiers=mods))

    return steps
