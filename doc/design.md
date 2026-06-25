# AI assisted development stages

## Stage 1: optionally work directly via touchy-pad API

Originally this project talked to the StreamController app to do its work. We now
default to talking to **touchy-pad** devices instead, with a `--streamcontroller`
CLI flag to fall back to the old StreamController DBus API.

### Goal

Make touchy-pad the default backend. The autopage `.ap.toml` model
([`AutopageDef`](../src/autopage/toml.py)) stays the backend-neutral source of
truth; only the "render + deliver" layer changes per backend.

### Backend abstraction (the refactoring)

Today the pipeline is StreamController-specific end to end:

`parse_toml_*` → `AutopageDef` → `generate_page_json` (SC JSON) →
`push_jsonpage` → `StreamControllerClient.add_page`.

Introduce an abstract `ApiClient` base class that owns **both rendering and
delivery**, so each backend renders the neutral model in its native form:

```
ApiClient (ABC)                       # src/autopage/api_client.py
  ├─ render_page(AutopageDef, *, decks) -> artifact   # backend-native
  ├─ artifact_to_text(artifact) -> str                # for --dry-run
  ├─ push_page(name, artifact, *, force, known_pages)
  ├─ set_active_page(serial, name)
  ├─ get_controllers() -> list[str]
  ├─ get_pages() -> list[str]
  ├─ resolve_icons(AutopageDef)                        # default: no-op
  └─ listen_foreground(callback)                       # default: deferred

StreamControllerClient(ApiClient)     # src/autopage/sc_api_client.py  (moved)
TouchyApiClient(ApiClient)            # src/autopage/touchy/__init__.py (new)
```

`get_client()` becomes a factory that selects the backend (Touchy by default,
StreamController when `--streamcontroller` is passed). `engine.py` is rewritten
to drive the client through this interface rather than calling
`generate_page_json` / `add_page` directly. For the SC backend `render_page`
returns the existing JSON string (so behaviour is unchanged); for Touchy it
returns a touchy-pad `Widget`.

### TouchyApiClient rendering

Following [`touchydeck/layout.py`](../touchy-pad/app/src/touchy_pad/touchydeck/layout.py)
but using `image_button` widgets carrying macros (see
[`test.py`](../touchy-pad/app/src/touchy_pad/pages/test.py) and
[python-api.md](../touchy-pad/docs/python-api.md)):

* Tile **72×72** `image_button`s in a `grid`, computing `cols`/`rows` from the
  device panel size (`board_info.display_{width,height}`), exactly like
  `TouchyDeck._auto_grid`.
* Honour `Button.location` ("1x2") for placement; auto-fill the rest in
  row-major order (mirrors `generate_page_json`'s `_next_location`).
* Use a single **placeholder icon** for every button for now. Automatic
  Material Design icon selection comes in a later stage.
* Upload via `pad.user_screen_save(page_name, widget)`; activate with
  `pad.show_user_screen(page_name)`.

### Action mapping

autopage actions currently compile to **evdev** keycodes via
[`type_string_to_keys`](../src/autopage/keys.py), but touchy `macro_action`
takes **HID usage IDs** + a modifier bitmask
(`macros.key_tap(hid_keys.KEY_H, MOD_LSHIFT)`). A new
[`keys_hid.py`](../src/autopage/keys_hid.py) reuses the existing name/char
tables to emit HID `key_tap`/`key_down`/`key_up` macro steps.

StreamController-only actions (an explicit `action.id` + `settings`, e.g. a
plugin action) have no device-side equivalent. For these, attach a
`host_action(on_event=...)` callback that runs a **stub Python function on the
host emitting a log message**, so the button still does something visible and we
have a hook to flesh out later.

### Deferred to a later stage

* **Listen / auto-switch on Touchy.** The StreamController backend gets the
  foreground window from a DBus signal; touchy-pad has no equivalent. A later
  task adds a `kdotool`-based foreground-window source for app-change
  notifications. Until then `--listen` only works under `--streamcontroller`.
* Automatic Material Design icon selection.

### pyproject

Add a `touchy-pad` dependency, pointed at the local `touchy-pad/app` path during
development (the git submodule), switching to the PyPI release later.
