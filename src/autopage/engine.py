"""Autopage engine: orchestrates TOML parsing, JSON generation, and API calls."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import NamedTuple

from autopage.toml import AutopageDef, parse_toml_dict, parse_toml_file

log = logging.getLogger(__name__)

# Default remote URL for the autopage-recipes toml-repo index
REMOTE_RECIPES_URL = "https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main"
# The kind tag used to identify autopage recipe repos
AP_KIND = "ap"


# ── Icon resolution ──────────────────────────────────────────────────


def _build_icon_catalog(client=None) -> tuple[list[tuple[str, str]], str]:
    """Fetch all icon packs and their icons from StreamController.

    Args:
        client: An optional ``StreamControllerClient`` instance.  When *None*
                a new client is created (requires DBus).

    Returns a tuple of (catalog, data_path) where catalog is a list of
    ``(pack_id, icon_name)`` tuples and data_path is the base path
    from the StreamController API.
    """
    if client is None:
        from autopage.api_client import get_client

        client = get_client()

    data_path = "data"  # fallback
    try:
        data_path = client.get_data_path()
    except Exception as exc:
        log.warning("Could not fetch DataPath from StreamController: %s", exc)

    catalog: list[tuple[str, str]] = []
    try:
        for pack_id in client.get_icon_packs():
            log.debug("Fetching icons for pack %r", pack_id)
            for icon_name in client.get_icon_names(pack_id):
                catalog.append((pack_id, icon_name))
        log.info(
            "Icon catalog: %d icon(s) across %d pack(s)",
            len(catalog),
            len(set(p for p, _ in catalog)),
        )
    except Exception as exc:
        log.warning("Could not fetch icon catalog from StreamController: %s", exc)

    return catalog, data_path


def _match_icon(
    pattern: str, catalog: list[tuple[str, str]], data_path: str = "data"
) -> str | None:
    """Match an icon regex against the catalog and return the media path.

    The *pattern* is treated as a regex and matched (case-insensitively)
    against the icon name.  The first match wins.

    Args:
        pattern: Regex to match against icon names.
        catalog: List of (pack_id, icon_name) tuples.
        data_path: Base data path from the StreamController API.
    """
    regex = re.compile(pattern, re.IGNORECASE)

    for pack_id, icon_name in catalog:
        if regex.fullmatch(icon_name):
            # Build the full media path expected by StreamController.
            return os.path.join(data_path, "icons", pack_id, "icons", f"{icon_name}.png")

    return None


def _resolve_icons(definition: AutopageDef, *, client=None) -> None:
    """Resolve icon patterns on all buttons using the StreamController API.

    Args:
        definition: The parsed autopage definition whose buttons will be updated
                    in-place.
        client: An optional ``StreamControllerClient`` instance (for testing).

    Buttons whose icon cannot be resolved will have the icon dropped.
    """
    buttons_with_icons = [b for b in definition.buttons if b.icon]
    if not buttons_with_icons:
        return

    catalog, data_path = _build_icon_catalog(client)
    if not catalog:
        log.info("Icon catalog is empty, skipping icon resolution")
        return

    for button in buttons_with_icons:
        resolved = _match_icon(button.icon, catalog, data_path)
        if resolved:
            log.info("Resolved icon %r → %s", button.icon, resolved)
            button.icon = resolved
        else:
            log.warning("No icon matched pattern %r, dropping...", button.icon)
            button.icon = None


def _get_controller_serials() -> list[str]:
    """Fetch connected controller serial numbers, returning [] on failure."""
    try:
        from autopage.api_client import get_client

        client = get_client()
        serials = client.get_controllers()
        log.info("Found %d controller(s): %s", len(serials), serials)
        return serials
    except Exception as exc:
        log.warning("Could not fetch controllers from StreamController: %s", exc)
        return []


# ── Public API ───────────────────────────────────────────────────────


def toml_to_jsonpage(path: str | Path) -> tuple[str, object]:
    """Convert an ap.toml file to a backend-native page artifact.

    1. Parse the TOML definition.
    2. Let the active backend resolve icon hints.
    3. Render the backend-native page artifact.

    Returns a tuple of (page_name, artifact). The artifact is a JSON string
    for the StreamController backend or a touchy-pad ``Widget`` for the
    Touchy backend; pass it straight to :func:`push_jsonpage`.
    """
    from autopage.api_client import get_client

    path = Path(path)
    log.info("Loading autopage definition from %s", path)

    definition = parse_toml_file(path)

    client = get_client()

    # Let the backend resolve icon hints (StreamController matches against its
    # icon packs; other backends may no-op).
    client.resolve_icons(definition)

    # Fetch connected deck serial numbers for auto-change
    decks = _get_controller_serials()

    artifact = client.render_page(definition, decks=decks)

    # Derive a page name from the filename (strip .ap.toml suffix)
    page_name = path.stem
    if page_name.endswith(".ap"):
        page_name = page_name[: -len(".ap")]

    log.info("Generated page %r with %d button(s)", page_name, len(definition.buttons))

    return page_name, artifact


def _fetch_known_pages() -> set[str]:
    """Read the current Pages list from StreamController and return as a set."""
    from autopage.api_client import get_client

    try:
        client = get_client()
        pages = set(client.get_pages())
        log.info("Known pages on controller: %s", pages)
        return pages
    except Exception as exc:
        log.warning("Could not fetch existing pages: %s", exc)
        return set()


def push_jsonpage(
    page_name: str,
    artifact: object,
    *,
    force: bool = False,
    known_pages: set[str] | None = None,
) -> bool:
    """Push a rendered page artifact to the active backend.

    Args:
        page_name: Name of the page to create.
        artifact: Backend-native page artifact from :func:`toml_to_jsonpage`.
        force: If *True* and the page already exists, replace it.
        known_pages: Optional set of page names already on the target. If
                     provided and *force* is False, pages that already exist
                     are skipped. Newly pushed pages are added in-place.

    Returns:
        True if the page was actually pushed, False if it was skipped.
    """
    from autopage.api_client import get_client

    client = get_client()
    return client.push_page(page_name, artifact, force=force, known_pages=known_pages)


def _discover_ap_repos(dev: bool = False) -> list[object]:
    """Use toml-repo to discover all ap.toml repos.

    Args:
        dev: If True, use local ``file:autopage-recipes`` directory.
             Otherwise use the remote GitHub URL.

    Returns:
        A list of ``Repo`` objects whose kind is ``"ap"``.
    """
    from toml_repo import RepoManager, set_config_suffix

    set_config_suffix("ap.toml")

    if dev:
        # Resolve the local autopage-recipes directory relative to cwd
        local_path = Path("autopage-recipes").resolve()
        base_url = f"file://{local_path}"
    else:
        base_url = REMOTE_RECIPES_URL
    log.info("Discovering repos from %s (dev=%s)", base_url, dev)

    manager = RepoManager()
    _root = manager.add_repo(base_url)

    ap_repos = manager.get_repos_by_kind(AP_KIND)
    log.info("Found %d repo(s) of kind %r", len(ap_repos), AP_KIND)
    return ap_repos


def _page_name_from_url(url: str) -> str:
    """Derive a page name from a repo URL.

    Strips the directory path and the .ap.toml suffix.
    e.g. "file:///foo/bar/code.ap.toml" → "code"
    """
    from urllib.parse import urlparse

    basename = os.path.basename(urlparse(url).path)
    # Strip .ap.toml (or .toml) suffix
    name = basename
    if name.endswith(".ap.toml"):
        name = name[: -len(".ap.toml")]
    elif name.endswith(".toml"):
        name = name[: -len(".toml")]
    return name


def repo_to_jsonpage(repo) -> tuple[str, object]:
    """Convert a toml-repo Repo (with pre-parsed config) to a page artifact.

    Uses the already-parsed TOML data from the Repo object rather than
    re-reading from the filesystem.

    Returns a tuple of (page_name, artifact) (see :func:`toml_to_jsonpage`).
    """
    from autopage.api_client import get_client

    log.info("Building page from repo config: %s", repo.url)

    definition = parse_toml_dict(repo.config)
    definition.source_path = repo.url

    client = get_client()

    # Let the backend resolve icon hints.
    client.resolve_icons(definition)

    # Fetch connected deck serial numbers for auto-change
    decks = _get_controller_serials()

    artifact = client.render_page(definition, decks=decks)

    page_name = _page_name_from_url(repo.url)
    log.info("Generated page %r with %d button(s)", page_name, len(definition.buttons))

    return page_name, artifact


def process_all_repos(*, dev: bool = False, dry_run: bool = False, force: bool = False) -> None:
    """Discover all ap.toml repos via toml-repo and process each one.

    This is the main entry-point used when no explicit source file is
    provided on the command line.

    Args:
        dev: If True, use local autopage-recipes instead of remote.
        dry_run: If True, print JSON instead of pushing to StreamController.
        force: If True, replace pages that already exist.
    """
    from autopage.api_client import get_client

    ap_repos = _discover_ap_repos(dev=dev)

    if not ap_repos:
        log.warning("No repos of kind %r found. Nothing to do.", AP_KIND)
        return

    known_pages = _fetch_known_pages() if not dry_run else set()

    client = get_client() if dry_run else None
    for i, repo in enumerate(ap_repos, 1):
        log.info("Processing repo %d/%d: %s", i, len(ap_repos), repo.url)
        try:
            page_name, artifact = repo_to_jsonpage(repo)
            if dry_run:
                print(client.artifact_to_text(artifact))
            else:
                push_jsonpage(page_name, artifact, force=force, known_pages=known_pages)
        except Exception as exc:
            log.error("Error processing repo %s: %s", repo.url, exc)


# ── Prepared page entry for listen mode ──────────────────────────────


class _PreparedPage(NamedTuple):
    """A pre-parsed page with its match rules, ready for window matching."""

    page_name: str
    definition: AutopageDef
    repo: object  # the toml-repo Repo object (kept for rebuild)


def _prepare_all_repos(dev: bool = False) -> list[_PreparedPage]:
    """Discover and parse all ap.toml repos, returning prepared pages.

    Each entry contains the parsed definition (with match rules) and the
    repo object so we can later generate JSON on demand.
    """
    ap_repos = _discover_ap_repos(dev=dev)
    prepared: list[_PreparedPage] = []

    for repo in ap_repos:
        try:
            definition = parse_toml_dict(repo.config)
            definition.source_path = repo.url
            page_name = _page_name_from_url(repo.url)
            prepared.append(_PreparedPage(page_name, definition, repo))
            log.info(
                "Prepared page %r with %d match rule(s)",
                page_name,
                len(definition.matches),
            )
        except Exception as exc:
            log.error("Error preparing repo %s: %s", repo.url, exc)

    return prepared


def _match_window(
    prepared_pages: list[_PreparedPage],
    window_name: str,
    window_class: str,
) -> list[_PreparedPage]:
    """Return all prepared pages whose match rules match the given window."""
    matched: list[_PreparedPage] = []

    for entry in prepared_pages:
        for rule in entry.definition.matches:
            try:
                if rule.class_pattern and re.fullmatch(
                    rule.class_pattern, window_class, re.IGNORECASE
                ):
                    matched.append(entry)
                    break
                if rule.name_pattern and re.fullmatch(
                    rule.name_pattern, window_name, re.IGNORECASE
                ):
                    matched.append(entry)
                    break
            except re.error as exc:
                log.warning("Bad regex in page %r: %s", entry.page_name, exc)

    return matched


def _activate_page_on_all_controllers(page_name: str) -> None:
    """Set the given page as active on every connected controller."""
    from autopage.api_client import get_client

    client = get_client()
    try:
        serials = client.get_controllers()
    except Exception as exc:
        log.warning("Could not fetch controllers: %s", exc)
        return

    for serial in serials:
        try:
            client.set_active_page(serial, page_name)
            log.info("Set active page %r on controller %s", page_name, serial)
        except Exception as exc:
            log.warning("Failed to set active page on controller %s: %s", serial, exc)


def listen_and_autoswitch(*, dev: bool = False, force: bool = False) -> None:
    """Listen for ForegroundWindow changes and auto-switch pages.

    1. Discover and pre-parse all ap.toml files (like process_all_repos).
    2. Start listening for DBus property changes on the StreamController service.
    3. When ForegroundWindow changes, check all match rules.
    4. For each matching page, push it (respecting --force) and set it active
       on all controllers.
    """
    from autopage.api_client import get_client

    prepared_pages = _prepare_all_repos(dev=dev)
    if not prepared_pages:
        log.warning("No ap.toml repos found. Nothing to listen for.")
        return

    # Snapshot which pages the controller already has so we can skip
    # redundant pushes (unless --force).
    known_pages = _fetch_known_pages()

    log.info(
        "Loaded %d page(s) with match rules, %d page(s) already on controller. "
        "Listening for window changes...",
        len(prepared_pages),
        len(known_pages),
    )

    def on_window_changed(window_name, window_class):
        log.info("Window changed: name=%r class=%r", window_name, window_class)

        matched = _match_window(prepared_pages, window_name, window_class)

        if not matched:
            log.debug("No matching pages for current window")
            return

        for entry in matched:
            try:
                page_name = _page_name_from_url(entry.repo.url)
                if not force and page_name in known_pages:
                    log.debug(
                        "Page %r already on controller, skipping rebuild",
                        page_name,
                    )
                else:
                    # create a new page and switch to it
                    page_name, artifact = repo_to_jsonpage(entry.repo)
                    pushed = push_jsonpage(
                        page_name, artifact, force=force, known_pages=known_pages
                    )
                    if pushed:
                        _activate_page_on_all_controllers(page_name)
                        log.info("Switched to page %r", page_name)
                    else:
                        log.debug(
                            "Page %r already on controller, skipping activation",
                            page_name,
                        )
            except Exception as exc:
                log.error("Error pushing page %r: %s", entry.page_name, exc)

    client = get_client()
    client.listen_foreground(on_window_changed)
