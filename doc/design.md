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

* Automatic Material Design icon selection.

### pyproject

Add a `touchy-pad` dependency, pointed at the local `touchy-pad/app` path during
development (the git submodule), switching to the PyPI release later.

## Stage 2: use material design icons in our Touchy-pad version

Instead of the placeholder icon use the
[python-material-icons](https://pypi.org/project/python-material-icons/) library
to generate icon images and apply those images to our image buttons.

### Background

`python-material-icons` (imported as `material_icons`) exposes a single
`MaterialIcons` class whose `get()` method renders an icon name to PNG bytes:

```python
from material_icons import MaterialIcons, IconStyle
icons = MaterialIcons()
png_bytes = icons.get("content_copy", size=72, color="#ffffff",
                      style=IconStyle.OUTLINED)
```

It caches on `(name, size, color, style)`, and raises `FileNotFoundError` for
unknown icon names. The autopage `Button.icon` field already carries Material
Design icon names verbatim (`content_copy`, `home`, `arrow_back`, …), so no name
translation is needed.

The touchy `image_button(asset=...)` accepts a path string, raw image `bytes`,
or a `PIL.Image` (via `coerce_image_source`). Passing PNG `bytes` directly is
the simplest path: the bytes are wrapped in a single-use `ImageSource` and
uploaded to the device automatically when `user_screen_save` binds the widget.
That means dry-run rendering works with no device attached.

### Approach

1. **New module `src/autopage/touchy/icons.py`** — a thin wrapper around
   `MaterialIcons`:
   * a lazily-created module-level `MaterialIcons` singleton;
   * `render_icon(name, *, size=KEY_PIXELS, color=DEFAULT_ICON_COLOR, style=DEFAULT_ICON_STYLE) -> bytes | None`
     that returns PNG bytes, normalising the name (lower-case, spaces/hyphens to
     underscores) and returning `None` (with a warning) when the icon is unknown
     or the library is missing, so callers can fall back to the placeholder;
   * module constants `DEFAULT_ICON_COLOR = "#ffffff"` and
     `DEFAULT_ICON_STYLE = IconStyle.OUTLINED` (white outlined icons read well on
     the coloured button backgrounds).

2. **`src/autopage/touchy/render.py`** — in `render_widget`, for each placed
   button choose the `image_button` asset:
   * if `button.icon` is set, call `render_icon(button.icon)`; on success pass
     the PNG `bytes` as the asset, otherwise fall back to `placeholder_path`;
   * buttons with no `icon` keep using `placeholder_path`.

   The `button.size` hint is still ignored for now (icons render at the native
   key size); it can scale the rendered icon later.

3. Keep the placeholder upload in `TouchyApiClient.push_page` as the fallback
   asset for icon-less / unresolved buttons.

No changes are needed in the StreamController backend (it resolves icons via its
own DBus icon catalog), nor in `engine.resolve_icons` (touchy renders icons at
draw time rather than pre-resolving them).

## Stage 3: use kdotool to see foreground app changes

### Goal

Make `autopage --listen` work with the default **touchy-pad** backend. Today
auto-switch only works under `--streamcontroller`, because the foreground
window comes from a StreamController DBus signal that touchy-pad has no
equivalent for. We add a polling foreground-window *source* (`kdotool` on KDE
Wayland) and wire it into `TouchyApiClient.listen_foreground`, so that:

> **When the foreground app changes, if some `ap.toml` page's match rules match
> that window, tell the touchy device to switch to that user-screen.**

The matching + activation loop already exists and is backend-neutral
([`engine.listen_and_autoswitch`](../src/autopage/engine.py)); the only missing
piece for Touchy is a `listen_foreground` implementation, plus one fix so a
match **always activates** the page (see "Engine fix" below).

### Background — how kdotool reports the active window

`kdotool` chains subcommands left-to-right against a selected window. The
active-window query prints one line per query subcommand, in order:

```bash
$ kdotool getactivewindow getwindowid getwindowclassname getwindowname
{58057643-494f-43df-89c8-9660f91a8cdf}                         # window id
code                                                           # WM class
Extension: CMake Tools - touchy-pad … - Visual Studio Code     # window title
```

Environment requirements (already handled by the Fedora devcontainer, see
`.devcontainer/fedora/`): `kdotool` must be on `PATH`, `DBUS_SESSION_BUS_ADDRESS`
must point at the host session bus, and `TMPDIR` must be a host-shared dir
(kdotool round-trips a temp file written by KWin). With no active window /
no compositor, kdotool exits non-zero or prints nothing — treated as "unknown".

### 1. New module `src/autopage/foreground.py` (the OS-neutral source)

A small abstraction so macOS / Windows / GNOME backends can slot in later:

```python
@dataclass(frozen=True)
class WindowInfo:
    id: str
    window_class: str
    name: str

class ForegroundSource(ABC):
    @abstractmethod
    def get_active_window(self) -> WindowInfo | None: ...
    """Return the current foreground window, or None if unknown."""

def get_default_source() -> ForegroundSource:
    """Pick a source for this host (today: KdotoolSource)."""
```

`KdotoolSource(ForegroundSource)`:

* Resolves the executable once via `shutil.which("kdotool")` (overridable arg),
  raising a clear error if missing.
* `get_active_window()` runs
  `kdotool getactivewindow getwindowid getwindowclassname getwindowname`
  with a short timeout (`subprocess.run(..., capture_output=True, text=True,
  timeout=...)`), splits stdout into lines, and maps them positionally to
  `WindowInfo(id, window_class, name)`. Returns `None` on non-zero exit,
  timeout, or fewer lines than expected (no crash — auto-switch just idles).
* No global state; cheap to call once per second.

> Naming: the Stage 3 sketch said `kdotool.py`, but a `kdotool`-named module
> would shadow the executable in tooling/output and bakes the backend into the
> name. `foreground.py` with a `KdotoolSource` class keeps the future
> multi-OS abstraction the sketch explicitly asked for.

### 2. `TouchyApiClient.listen_foreground` (poll → dispatch on change)

Mirror the *contract* of `StreamControllerClient.listen_foreground`
(`callback(window_name, window_class)`), but drive it by polling instead of a
DBus signal:

* Build a `ForegroundSource` (`foreground.get_default_source()`), default poll
  interval **1.0s** (constant, easily tunable).
* Loop: every interval, read `get_active_window()`. Keep the last-seen
  `(window_class, name)`; only invoke `callback` when it **changes** (edge-
  triggered, exactly like the DBus signal — avoids re-pushing every second).
* Block until `KeyboardInterrupt`, matching the SC backend's blocking `listen`.
* Tolerate transient `None`/errors from the source (log at debug, keep polling).

No change to the `ApiClient` ABC is required — `listen_foreground(callback)` is
already declared there.

### 3. Engine fix — a match must **always** switch the device

The user-visible requirement is "foreground changes → switch to the matching
user-screen." Today [`engine.listen_and_autoswitch`](../src/autopage/engine.py)
only calls `_activate_page_on_all_controllers` **inside** the "page was just
pushed" branch; when the matching page is already on the device
(`page_name in known_pages` and not `--force`) it logs *"skipping activation"*
and never switches. That's correct for "avoid rebuilding", but wrong for "switch
to it".

Fix: decouple **push** from **activate** in `on_window_changed`:

1. Ensure the page exists on the device — push only if unknown or `--force`
   (unchanged dedupe via `known_pages`).
2. **Always** call `set_active_page` for the matched page afterwards.
3. Track the currently-active page name and skip the redundant
   `set_active_page` when it already matches, so a title-only change that maps
   to the already-active page doesn't re-send `show_user_screen` each second.

For Touchy this lands as `pad.show_user_screen(page_name)` (via
`set_active_page` → existing impl); for StreamController behaviour is unchanged
(it always re-activated through the same path). `get_controllers()` already
returns `["touchy-pad"]`, so `_activate_page_on_all_controllers` works as-is.

### 4. CLI / docs

* `--listen` already exists and is backend-neutral; drop the Stage 1 caveat that
  it "only works under `--streamcontroller`". No new flags required. (Optionally
  expose `--poll-interval`, default 1.0s, if we want it tunable from the CLI.)
* Note the kdotool/devcontainer env requirements in the autopage README.

### 5. Tests

* `foreground.py`: monkeypatch `subprocess.run` to return canned stdout and
  assert `WindowInfo` parsing; assert `None` on non-zero exit / timeout /
  short output; assert `which` lookup + missing-binary error.
* `listen_foreground`: inject a fake `ForegroundSource` yielding a scripted
  sequence of windows and assert the callback fires **only on change**.
* Engine: assert that a match whose page is already in `known_pages` still
  calls `set_active_page` (regression test for the fix), and that an unchanged
  active page is not re-activated.

### Deferred

* Non-KDE sources (GNOME via extension/`gdbus`, macOS, Windows) — the
  `ForegroundSource` ABC is the seam for these.
* Event-driven (vs. polled) window changes on KDE, if kdotool/KWin grows a
  signal we can subscribe to.

## Stage 4: make background graphics work

**Status: done.** Implemented per the plan below (`toml.background_url`,
`touchy/background.fetch_background`, `render_widget(background_path=...)`
absolute-layout composite, and `TouchyApiClient` fetch+cache via `ImageCache`).
39 tests pass, ruff clean. Hardware open-detail (absolute root fill) noted below
still to confirm on-device.

### Goal

Honour a page-level background image on the **touchy-pad** backend. When an
`ap.toml` declares

```toml
[background]
url = "https://www.geeksville.com/robots.png"
```

the rendered user-screen draws that image scaled to fit the page body, with the
button grid composited on top. Per-button `opacity` (already supported) lets the
background show through. Non-touchy (StreamController) backends are out of scope
for this stage.

> The example file [`doc/example-shell.ap.toml`](example-shell.ap.toml) already
> documents `[background] url`, but `parse_toml_dict` silently drops it today —
> there is no `background` field on `AutopageDef`.

### Background — existing building blocks

* **HTTP fetch.** The CLI's `touchpad_image(url)`
  ([`app/src/touchy_pad/cli.py`](../../../app/src/touchy_pad/cli.py)) fetches a
  URL with `urllib.request` (stdlib) using a browser `User-Agent` and a timeout,
  then hands the raw bytes to the image pipeline. Pillow (`Image.open`) decodes
  PNG / JPEG / GIF / BMP / WebP; GIFs stay animated (`lv_gif`), everything else
  becomes an LVGL `.bin`. We reuse the same fetch shape but **must not** write to
  an `F:` path manually.
* **Cached image upload.** `ImageCache`
  ([`app/src/touchy_pad/api/image_cache.py`](../../../app/src/touchy_pad/api/image_cache.py))
  `.set_cached_image(data)` normalises a `PIL.Image` / `bytes` (PNG / JPEG / GIF
  / …), content-hash-dedups, uploads once to the transient `T:host/icache/`
  drive, and **returns the device path** (with the right suffix). Crucially it
  **passes GIFs through verbatim with a `.gif` suffix** — the firmware's native
  `lv_gif` decoder then animates them with no extra work (`is_gif` →
  `rescale_gif` fit; everything else → `to_lvgl_bin` `.bin`). This is the
  path-based route the background should use.
* **Why not the dynamic `ImageSource` route.** `screens.image(asset=...)` also
  accepts an `ImageSource` / bare `PIL.Image` / `bytes`, but that path always
  encodes through `to_lvgl_bin` → a `.bin` at a `.bin` path, which **flattens an
  animated GIF to a single frame**. So for backgrounds we upload via
  `ImageCache` (path-based, GIF-preserving) and hand `image()` the returned
  **path string**, rather than passing bytes/`ImageSource`.
* **Grid root.** `render_widget`
  ([`src/autopage/touchy/render.py`](../src/autopage/touchy/render.py)) builds a
  single `protobuf.Widget` with a `layout_grid` (`cols`×`rows`, gap `KEY_GAP`)
  whose children are the per-button `image_button`s in `cell(...)`s. This grid is
  what we layer on top of the background.

### 1. Parse `[background]` (`src/autopage/toml.py`)

* Add `background_url: str | None = None` to `AutopageDef`.
* In `parse_toml_dict`, read `doc.get("background", {}).get("url")` and store it
  on the result (alongside the existing `match` / `default` / `button` parsing).
* No `[default]`/merge interaction — it's a page-level field, like `matches`.

### 2. Fetch the image (`src/autopage/touchy/background.py`, new)

A tiny helper, isolated so the network dependency stays out of `render.py`. We do
**no** image processing of our own — `ImageCache` already normalises everything
(GIF passthrough, static → `.bin`, aspect-preserving downscale to its `max_dim`),
so we just fetch and hand it the raw bytes:

* `fetch_background(url) -> bytes | None` — fetch with `urllib.request` (same
  `User-Agent` + timeout pattern as `touchpad_image`) and return the raw bytes;
  return `None` (log a warning) on any network error — a missing background must
  never break rendering.

That's it: no Pillow, no GIF/static branching, no resize in our code. The cache's
`max_dim` does the sizing and its `is_gif` check keeps GIFs animated.

### 3. Composite background behind the grid

Upload happens where a device is available, so the fetch+cache lives in
`TouchyApiClient` ([`src/autopage/touchy/__init__.py`](../src/autopage/touchy/__init__.py)),
and `render_widget` ([`render.py`](../src/autopage/touchy/render.py)) stays pure
(takes an already-uploaded path):

* In `render_page` (which already has the connected pad via `_grid_dims`): if
  `definition.background_url` is set **and** a device is present, call
  `background.fetch_background(url)`, then
  `ImageCache(pad, max_dim=max(page_w, page_h)).set_cached_image(raw)` to get a
  device `background_path` (a `T:host/icache/<hash>.gif` or `.bin`, scaled
  aspect-preserving to the page). Pass it into `render_widget`.
* Compute the page body's pixel size from the grid geometry we already own:
  `page_w = cols * KEY_PIXELS + (cols + 1) * KEY_GAP`,
  `page_h = rows * KEY_PIXELS + (rows + 1) * KEY_GAP` (matching `auto_grid`'s
  pitch math).
* `render_widget(..., background_path: str | None = None)`: when a path is given,
  draw the image first and the grid second (LVGL paints siblings in child order,
  so later siblings cover earlier ones) by wrapping both in an **absolute-layout
  root** sized to the page:
  * background = `s.image(id="autopage_bg", asset=background_path,
    rect=s.rect(0, 0, page_w, page_h))` — a plain path string, so no re-encode
    and (for `.gif`) the firmware animates it for free. The cached bitmap is
    aspect-fit to the page, so it sits centred in the full-page rect.
  * `root = protobuf.Widget(id="autopage_root")`, `s.absolute()` layout,
    `root.rect = s.rect(0, 0, page_w, page_h)`, children `[background, grid]`.
    The grid is re-parented `id="autopage_root"` → `id="autopage_grid"` with
    `rect=s.rect(0, 0, page_w, page_h)` so it overlays the full background.
* **No background** (`background_url` unset, no device, or fetch failed):
  `background_path` is `None` and `render_widget` returns the bare grid exactly
  as today — no wrapper, no asset cost. Common case unchanged.

> Open implementation detail to verify on hardware: whether the absolute root
> needs explicit `grow_x/grow_y` to fill the chrome's `widget_ref(id="page")`
> slot, or whether the fixed `rect` size suffices. The grid path already fills
> the slot via grid layout; the wrapped path must match. Fallback if absolute
> sizing misbehaves: set the background as the **grid root's first child** under
> the existing grid by giving it a `cell` spanning all `cols`×`rows`
> (`col_span=cols, row_span=rows`, `grow_x/grow_y=1`) and adding it *before* the
> buttons so it paints underneath.

### 4. Caching / dry-run / failures

* One `ImageCache` per `TouchyApiClient` (or per render) → background uploaded
  once to `T:host/icache/`, content-hash-dedup avoids re-upload of identical
  bytes across pages/refreshes.
* `--dry-run` / no device: the fetch+cache is gated on a connected pad, so no
  network or upload happens — `background_path` is `None` and the page renders as
  the bare grid. (This sidesteps the earlier "should dry-run hit the network?"
  question entirely: it doesn't.)
* All failures (bad URL, timeout, decode error, unsupported format) degrade to
  "no background", logged at WARNING, page still renders.

### 5. Tests (`tools/autopage/tests/test_autopage.py`)

* `toml`: `[background] url = "..."` parses into `AutopageDef.background_url`;
  absent table → `None`.
* `background.py`: monkeypatch `urllib.request.urlopen` to return canned bytes →
  `fetch_background` returns them; network error → `None`. (No normalisation to
  test — that lives in `ImageCache`, already covered by
  `app/tests/test_image_cache.py`.)
* `render`: call `render_widget(..., background_path="T:host/icache/x.gif")` and
  assert the root is the absolute wrapper whose first child is the background
  image (with that path) and second is the grid; with `background_path=None`,
  assert the root is the bare grid (unchanged).

### Deferred

* Background on non-touchy (StreamController) backends.
* Per-button background images (only page-level for this stage).
* Pixel-perfect *stretch* / cover-with-crop (today backgrounds are
  aspect-preserving fit via `ImageCache(max_dim=...)`, so a non-page-aspect image
  is centred with margins rather than filling edge to edge).

## TBD

INFO: Window changed: name='Glyphica' class='steam_app_2400160'