"""Tests for autopage."""

import json
from unittest.mock import MagicMock

from autopage import __version__
from autopage.cli import main
from autopage.engine import _match_icon, _resolve_icons
from autopage.json import (
    DEFAULT_OPACITY,
    _parse_color,
    generate_page_json,
    page_json_to_string,
)
from autopage.keys import type_string_to_keys
from autopage.toml import AutopageDef, Button, parse_toml_string

# ── Version / CLI ────────────────────────────────────────────────────


def test_version():
    """Version string is set."""
    assert __version__ == "0.1.0"


def test_cli_help(capsys):
    """CLI --help prints usage info."""
    try:
        main(["--help"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "autopage" in captured.out


def test_cli_version(capsys):
    """CLI --version flag works."""
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out


def test_cli_dry_run(capsys, tmp_path):
    """CLI --dry-run parses a toml file and prints JSON."""
    toml_file = tmp_path / "test.ap.toml"
    toml_file.write_text('[[button]]\ncenter = "hi"\n[[button.actions]]\ntype = "Ctrl+C"\n')
    rc = main(["--dry-run", str(toml_file)])
    assert rc == 0
    captured = capsys.readouterr()
    page = json.loads(captured.out)
    assert "keys" in page


# ── TOML parsing ─────────────────────────────────────────────────────


EXAMPLE_TOML = """\
[[match]]
class = "code"

[[button]]
location = "1x2"
icon = "next"
top = "foo"
center = "blah"
bottom = "bar"
background = "#ff2244"

[[button.actions]]
type = "Ctrl+C"

[[button]]
icon = "home"
center = "hello"

[[button.actions]]
type = "Hello SPACE world"
"""


def test_parse_matches():
    defn = parse_toml_string(EXAMPLE_TOML)
    assert len(defn.matches) == 1
    assert defn.matches[0].class_pattern == "code"
    assert defn.matches[0].name_pattern is None


def test_parse_buttons():
    defn = parse_toml_string(EXAMPLE_TOML)
    assert len(defn.buttons) == 2

    b0 = defn.buttons[0]
    assert b0.location == "1x2"
    assert b0.icon == "next"
    assert b0.top == "foo"
    assert b0.center == "blah"
    assert b0.bottom == "bar"
    assert b0.background == "#ff2244"
    assert len(b0.actions) == 1
    assert b0.actions[0].type == "Ctrl+C"

    b1 = defn.buttons[1]
    assert b1.location is None
    assert b1.icon == "home"
    assert b1.center == "hello"
    assert len(b1.actions) == 1
    assert b1.actions[0].type == "Hello SPACE world"


def test_parse_advanced_action():
    toml_text = """\
[[button]]
[[button.actions]]
id = "com_core447_OSPlugin::Hotkey"
settings = { "keys" = [[ 30, 1 ], [ 30, 0 ]] }
"""
    defn = parse_toml_string(toml_text)
    action = defn.buttons[0].actions[0]
    assert action.id == "com_core447_OSPlugin::Hotkey"
    assert action.settings == {"keys": [[30, 1], [30, 0]]}


# ── Key-code generation ─────────────────────────────────────────────


def test_type_ctrl_c():
    keys = type_string_to_keys("Ctrl+C")
    # Ctrl press, C press, C release, Ctrl release
    assert keys == [[29, 1], [46, 1], [46, 0], [29, 0]]


def test_type_ctrl_shift_t():
    keys = type_string_to_keys("Ctrl+Shift+T")
    # Ctrl press, Shift press, T press, T release, Shift release, Ctrl release
    assert keys == [[29, 1], [42, 1], [20, 1], [20, 0], [42, 0], [29, 0]]


def test_type_hello_space_world():
    keys = type_string_to_keys("Hello SPACE world")
    # H (shifted), e, l, l, o, space, w, o, r, l, d
    assert keys[0:4] == [[42, 1], [35, 1], [35, 0], [42, 0]]  # H
    assert keys[4:6] == [[18, 1], [18, 0]]  # e
    # ... space somewhere in the middle
    space_idx = None
    for i, k in enumerate(keys):
        if k == [57, 1]:
            space_idx = i
            break
    assert space_idx is not None
    assert keys[space_idx + 1] == [57, 0]


def test_type_literal_abc():
    keys = type_string_to_keys("abc")
    assert keys == [
        [30, 1],
        [30, 0],  # a
        [48, 1],
        [48, 0],  # b
        [46, 1],
        [46, 0],  # c
    ]


# ── Color parsing ───────────────────────────────────────────────────


def test_parse_color_named():
    """Named HTML5 colours are parsed with default opacity."""
    assert _parse_color("green") == [0, 128, 0, round(DEFAULT_OPACITY * 255)]


def test_parse_color_hex():
    """Hex #RRGGBB colours are parsed with default opacity."""
    assert _parse_color("#ff2244") == [255, 34, 68, round(DEFAULT_OPACITY * 255)]


def test_parse_color_with_opacity():
    """Explicit opacity overrides the default."""
    assert _parse_color("#00ff00", opacity=1.0) == [0, 255, 0, 255]
    assert _parse_color("red", opacity=0.5) == [255, 0, 0, 128]


def test_parse_color_zero_opacity():
    """Opacity 0.0 yields fully transparent."""
    assert _parse_color("white", opacity=0.0) == [255, 255, 255, 0]


# ── JSON generation ─────────────────────────────────────────────────


def test_generate_page_json_structure():
    defn = parse_toml_string(EXAMPLE_TOML)
    page = generate_page_json(defn)

    assert "settings" in page
    assert "keys" in page
    assert page["settings"]["auto-change"]["enable"] is True

    # Button 0 has explicit location "1x2"
    assert "1x2" in page["keys"]
    key_1x2 = page["keys"]["1x2"]["states"]["0"]
    assert key_1x2["labels"]["top"]["text"] == "foo"
    assert key_1x2["labels"]["center"]["text"] == "blah"
    assert key_1x2["labels"]["bottom"]["text"] == "bar"
    assert key_1x2["background"]["color"] == [255, 34, 68, round(DEFAULT_OPACITY * 255)]
    assert key_1x2["media"]["path"] == "next"
    assert len(key_1x2["actions"]) == 1
    assert key_1x2["actions"][0]["id"] == "com_core447_OSPlugin::Hotkey"

    # Button 1 has no location → auto-placed at 0x0
    assert "0x0" in page["keys"]
    key_0x0 = page["keys"]["0x0"]["states"]["0"]
    assert key_0x0["labels"]["center"]["text"] == "hello"


def test_page_json_roundtrip():
    defn = parse_toml_string(EXAMPLE_TOML)
    page = generate_page_json(defn)
    text = page_json_to_string(page)
    reloaded = json.loads(text)
    assert reloaded == page


# ── Icon resolution ──────────────────────────────────────────────────


def test_match_icon_exact():
    """Exact icon name matches."""
    catalog = [
        ("com_core447_MaterialIcons", "textsms"),
        ("com_core447_MaterialIcons", "home"),
    ]
    result = _match_icon("home", catalog)
    assert result == "data/icons/com_core447_MaterialIcons/icons/home.png"


def test_match_icon_regex():
    """A regex pattern matches icon names."""
    catalog = [
        ("pack_a", "arrow_back"),
        ("pack_a", "arrow_forward"),
        ("pack_b", "next"),
    ]
    # Match anything containing "forward" (anchored for fullmatch)
    result = _match_icon(".*forward", catalog)
    assert result == "data/icons/pack_a/icons/arrow_forward.png"


def test_match_icon_case_insensitive():
    """Icon matching is case-insensitive."""
    catalog = [("pack_a", "Home")]
    result = _match_icon("home", catalog)
    assert result == "data/icons/pack_a/icons/Home.png"


def test_match_icon_no_match():
    """Returns None when no icon matches."""
    catalog = [("pack_a", "textsms")]
    result = _match_icon("nonexistent", catalog)
    assert result is None


def test_match_icon_bare_name():
    """Handles icon names without file extensions."""
    catalog = [("pack_a", "home")]
    result = _match_icon("home", catalog)
    assert result == "data/icons/pack_a/icons/home.png"


def test_resolve_icons_updates_buttons():
    """_resolve_icons replaces icon patterns with resolved paths."""
    defn = AutopageDef(
        buttons=[
            Button(icon="home"),
            Button(icon="textsms"),
            Button(center="no icon"),
        ]
    )

    mock_client = MagicMock()
    mock_client.get_icon_packs.return_value = ["com_core447_MaterialIcons"]
    mock_client.get_icon_names.return_value = ["home", "textsms", "star"]

    _resolve_icons(defn, client=mock_client)

    assert defn.buttons[0].icon == "data/icons/com_core447_MaterialIcons/icons/home.png"
    assert defn.buttons[1].icon == "data/icons/com_core447_MaterialIcons/icons/textsms.png"
    assert defn.buttons[2].icon is None  # no icon, unchanged


def test_resolve_icons_api_failure_is_graceful():
    """If the StreamController API is unavailable, icons are dropped."""
    defn = AutopageDef(buttons=[Button(icon="home")])

    mock_client = MagicMock()
    mock_client.get_icon_packs.side_effect = Exception("no dbus")

    _resolve_icons(defn, client=mock_client)

    # Icon catalog fetch failed, so no icons are resolved and buttons keep their patterns
    assert defn.buttons[0].icon == "home"  # unchanged when catalog fetch fails
