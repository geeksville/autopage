"""Tests for autopage."""

import json
from unittest.mock import MagicMock

from autopage import __version__
from autopage.cli import main
from autopage.color import DEFAULT_OPACITY, parse_color_rgba
from autopage.engine import _match_icon, _resolve_icons
from autopage.json import (
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
    """CLI --dry-run parses a toml file and prints JSON (StreamController backend)."""
    toml_file = tmp_path / "test.ap.toml"
    toml_file.write_text('[[button]]\ncenter = "hi"\n[[button.actions]]\ntype = "Ctrl+C"\n')
    rc = main(["--dry-run", "--streamcontroller", str(toml_file)])
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
    assert parse_color_rgba("green") == [0, 128, 0, round(DEFAULT_OPACITY * 255)]


def test_parse_color_hex():
    """Hex #RRGGBB colours are parsed with default opacity."""
    assert parse_color_rgba("#ff2244") == [255, 34, 68, round(DEFAULT_OPACITY * 255)]


def test_parse_color_with_opacity():
    """Explicit opacity overrides the default."""
    assert parse_color_rgba("#00ff00", opacity=1.0) == [0, 255, 0, 255]
    assert parse_color_rgba("red", opacity=0.5) == [255, 0, 0, 128]


def test_parse_color_zero_opacity():
    """Opacity 0.0 yields fully transparent."""
    assert parse_color_rgba("white", opacity=0.0) == [255, 255, 255, 0]


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


def test_match_icon_custom_data_path():
    """Data path from API is used in icon paths."""
    catalog = [
        ("com_core447_MaterialIcons", "home"),
    ]
    result = _match_icon(
        "home",
        catalog,
        data_path="/home/user/.var/app/com.core447.StreamController/data",
    )
    assert result == (
        "/home/user/.var/app/com.core447.StreamController/data/icons/"
        "com_core447_MaterialIcons/icons/home.png"
    )


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
    mock_client.get_data_path.return_value = "data"
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
    mock_client.get_data_path.return_value = "data"
    mock_client.get_icon_packs.side_effect = Exception("no dbus")

    _resolve_icons(defn, client=mock_client)

    # Icon catalog fetch failed, so no icons are resolved and buttons keep their patterns
    assert defn.buttons[0].icon == "home"  # unchanged when catalog fetch fails


# ── Foreground source (kdotool) ──────────────────────────────────────


def _fake_completed(stdout="", returncode=0, stderr=""):
    """Build a stand-in for subprocess.CompletedProcess."""
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


def test_kdotool_parses_active_window(monkeypatch):
    """KdotoolSource maps the four output lines positionally (incl. pid)."""
    from autopage import foreground

    out = "{abc-123}\ncode\nSome Title\n4321\n"
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _fake_completed(stdout=out)

    monkeypatch.setattr(foreground.shutil, "which", lambda _: "/usr/bin/kdotool")
    monkeypatch.setattr(foreground.subprocess, "run", fake_run)

    win = foreground.KdotoolSource().get_active_window()
    assert win == foreground.WindowInfo(
        id="{abc-123}", window_class="code", name="Some Title", pid=4321
    )
    # pid query is part of the chained command.
    assert "getwindowpid" in captured["cmd"]


def test_kdotool_pid_optional(monkeypatch):
    """A missing or non-integer pid line yields pid=None, not a crash."""
    from autopage import foreground

    monkeypatch.setattr(foreground.shutil, "which", lambda _: "/usr/bin/kdotool")

    # Only three lines (no pid).
    monkeypatch.setattr(
        foreground.subprocess,
        "run",
        lambda *a, **k: _fake_completed(stdout="{id}\nfirefox\nTitle\n"),
    )
    win = foreground.KdotoolSource().get_active_window()
    assert win is not None
    assert win.pid is None

    # Non-integer pid.
    monkeypatch.setattr(
        foreground.subprocess,
        "run",
        lambda *a, **k: _fake_completed(stdout="{id}\nfirefox\nTitle\nnope\n"),
    )
    assert foreground.KdotoolSource().get_active_window().pid is None


def test_kdotool_none_on_failure(monkeypatch):
    """Non-zero exit, timeout, and short output all map to None."""
    import subprocess as _subprocess

    from autopage import foreground

    monkeypatch.setattr(foreground.shutil, "which", lambda _: "/usr/bin/kdotool")
    src = foreground.KdotoolSource()

    monkeypatch.setattr(foreground.subprocess, "run", lambda *a, **k: _fake_completed(returncode=1))
    assert src.get_active_window() is None

    def _raise_timeout(*a, **k):
        raise _subprocess.TimeoutExpired(cmd="kdotool", timeout=5.0)

    monkeypatch.setattr(foreground.subprocess, "run", _raise_timeout)
    assert src.get_active_window() is None

    monkeypatch.setattr(
        foreground.subprocess, "run", lambda *a, **k: _fake_completed(stdout="{id}\n")
    )
    assert src.get_active_window() is None


def test_kdotool_missing_binary(monkeypatch):
    """Constructing the source without kdotool on PATH raises clearly."""
    from autopage import foreground

    monkeypatch.setattr(foreground.shutil, "which", lambda _: None)
    try:
        foreground.KdotoolSource()
    except FileNotFoundError as exc:
        assert "kdotool" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


# ── TouchyApiClient.listen_foreground (poll → dispatch on change) ─────


class _ScriptedSource:
    """A ForegroundSource yielding a fixed sequence, then None forever."""

    def __init__(self, windows):
        self._windows = list(windows)

    def get_active_window(self):
        if self._windows:
            return self._windows.pop(0)
        return None


def test_listen_foreground_edge_triggered(monkeypatch):
    """Callback fires only when the (class, name) changes."""
    from autopage import foreground
    from autopage.touchy import TouchyApiClient

    win_a = foreground.WindowInfo(id="1", window_class="code", name="A", pid=1)
    win_a2 = foreground.WindowInfo(id="1", window_class="code", name="A", pid=1)
    win_b = foreground.WindowInfo(id="2", window_class="firefox", name="B", pid=2)

    source = _ScriptedSource([win_a, win_a2, win_b])
    monkeypatch.setattr(foreground, "get_default_source", lambda: source)

    # Drive the poll loop synchronously: each sleep advances, then stop.
    calls = []
    state = {"n": 0}

    def fake_sleep(_):
        state["n"] += 1
        if state["n"] >= 4:
            raise KeyboardInterrupt

    import autopage.touchy as touchy_mod

    monkeypatch.setattr(touchy_mod.time, "sleep", fake_sleep)

    client = TouchyApiClient()
    client.listen_foreground(lambda name, cls: calls.append((cls, name)))

    # win_a fires once; win_a2 is identical (no fire); win_b fires once.
    assert calls == [("code", "A"), ("firefox", "B")]


# ── Engine: a match always activates the page ────────────────────────


class _RecordingClient:
    """A fake ApiClient capturing set_active_page calls."""

    def __init__(self):
        self.activations = []

    def get_controllers(self):
        return ["touchy-pad"]

    def set_active_page(self, serial, name):
        self.activations.append((serial, name))


def _drive_listen(monkeypatch, *, windows, known_pages, force=False):
    """Run listen_and_autoswitch against scripted windows, return the client."""
    from autopage import api_client, engine
    from autopage.toml import AutopageDef, MatchRule

    page = engine._PreparedPage(
        page_name="code",
        definition=AutopageDef(matches=[MatchRule(class_pattern="code")]),
        repo=MagicMock(url="file:///x/code.ap.toml"),
    )
    monkeypatch.setattr(engine, "_prepare_all_repos", lambda dev=False: [page])
    monkeypatch.setattr(engine, "_fetch_known_pages", lambda: set(known_pages))

    client = _RecordingClient()

    def fake_listen(callback):
        for win in windows:
            callback(win.name, win.window_class)

    client.listen_foreground = fake_listen
    monkeypatch.setattr(api_client, "get_client", lambda: client)

    engine.listen_and_autoswitch(force=force)
    return client


def test_engine_activates_known_page(monkeypatch):
    """A match whose page is already on the device still activates it."""
    from autopage.foreground import WindowInfo

    win = WindowInfo(id="1", window_class="code", name="VS Code", pid=1)
    client = _drive_listen(monkeypatch, windows=[win], known_pages={"code"})

    assert client.activations == [("touchy-pad", "code")]


def test_engine_skips_redundant_activation(monkeypatch):
    """The same active page isn't re-activated on a title-only change."""
    from autopage.foreground import WindowInfo

    win1 = WindowInfo(id="1", window_class="code", name="VS Code - a", pid=1)
    win2 = WindowInfo(id="1", window_class="code", name="VS Code - b", pid=1)
    client = _drive_listen(monkeypatch, windows=[win1, win2], known_pages={"code"})

    # Activated once for win1; win2 maps to the same page → no re-activation.
    assert client.activations == [("touchy-pad", "code")]
