"""Parse .ap.toml autopage definition files using tomlkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomlkit


@dataclass
class MatchRule:
    """A window-matching rule."""

    class_pattern: str | None = None
    name_pattern: str | None = None


@dataclass
class Action:
    """A button action.

    Either *type* (shorthand for com_core447_OSPlugin::Hotkey)
    or *id* + *settings* (explicit plugin action).
    """

    type: str | None = None
    id: str | None = None
    settings: dict | None = None


@dataclass
class Button:
    """A single button definition."""

    location: str | None = None  # e.g. "1x2"
    icon: str | None = None
    top: str | None = None
    center: str | None = None
    bottom: str | None = None
    background: str | None = None  # RGBA hex like "0xff2244aa"
    actions: list[Action] = field(default_factory=list)


@dataclass
class AutopageDef:
    """A complete autopage definition parsed from an ap.toml file."""

    matches: list[MatchRule] = field(default_factory=list)
    buttons: list[Button] = field(default_factory=list)
    source_path: str | None = None


# ── Parsing ──────────────────────────────────────────────────────────


def parse_toml_file(path: str | Path) -> AutopageDef:
    """Parse an ap.toml file and return an AutopageDef."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        doc = tomlkit.load(f)

    result = parse_toml_dict(doc)
    result.source_path = str(path)
    return result


def parse_toml_string(text: str) -> AutopageDef:
    """Parse an ap.toml string and return an AutopageDef."""
    doc = tomlkit.parse(text)
    return parse_toml_dict(doc)


def parse_toml_dict(doc: dict) -> AutopageDef:
    """Parse a TOML document dict into an AutopageDef."""
    result = AutopageDef()

    # Parse [[match]] tables
    for m in doc.get("match", []):
        result.matches.append(
            MatchRule(
                class_pattern=m.get("class"),
                name_pattern=m.get("name"),
            )
        )

    # Parse [[button]] tables
    for b in doc.get("button", []):
        button = Button(
            location=b.get("location"),
            icon=b.get("icon"),
            top=b.get("top"),
            center=b.get("center"),
            bottom=b.get("bottom"),
            background=b.get("background"),
        )
        # Each button may have an [[button.action]] array
        for a in b.get("action", []):
            button.actions.append(
                Action(
                    type=a.get("type"),
                    id=a.get("id"),
                    settings=dict(a["settings"]) if "settings" in a else None,
                )
            )
        result.buttons.append(button)

    return result
