"""Autopage engine: orchestrates TOML parsing, JSON generation, and API calls."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from autopage.json import generate_page_json, page_json_to_string
from autopage.toml import AutopageDef, parse_toml_file

log = logging.getLogger(__name__)

# Default remote URL for the autopage-recipes toml-repo index
REMOTE_RECIPES_URL = (
    "https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main"
)
# The kind tag used to identify autopage recipe repos
AP_KIND = "ap"


# ── Icon resolution ──────────────────────────────────────────────────


def _build_icon_catalog(client=None) -> list[tuple[str, str]]:
    """Fetch all icon packs and their icons from StreamController.

    Args:
        client: An optional ``StreamControllerClient`` instance.  When *None*
                a new client is created (requires DBus).

    Returns a list of ``(pack_id, icon_name)`` tuples.
    """
    if client is None:
        from autopage.api_client import StreamControllerClient
        client = StreamControllerClient()

    catalog: list[tuple[str, str]] = []
    try:
        for pack_id in client.get_icon_packs():
            log.debug("Fetching icons for pack %r", pack_id)
            for icon_name in client.get_icon_names(pack_id):
                catalog.append((pack_id, icon_name))
        log.info("Icon catalog: %d icon(s) across %d pack(s)",
                len(catalog), len(set(p for p, _ in catalog)))
    except Exception as exc:
        log.warning("Could not fetch icon catalog from StreamController: %s", exc)

    return catalog


def _match_icon(pattern: str, catalog: list[tuple[str, str]]) -> str | None:
    """Match an icon regex against the catalog and return the media path.

    The *pattern* is treated as a regex and matched (case-insensitively)
    against the icon name.  The first match wins.
    """
    regex = re.compile(pattern, re.IGNORECASE)

    for pack_id, icon_name in catalog:
        if regex.fullmatch(icon_name):
            # Build the full media path expected by StreamController.
            return f"data/icons/{pack_id}/icons/{icon_name}.png"

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

    catalog = _build_icon_catalog(client)
    if not catalog:
        log.info("Icon catalog is empty, skipping icon resolution")
        return

    for button in buttons_with_icons:
        resolved = _match_icon(button.icon, catalog)
        if resolved:
            log.info("Resolved icon %r → %s", button.icon, resolved)
            button.icon = resolved
        else:
            log.warning("No icon matched pattern %r, dropping...", button.icon)
            button.icon = None


def _get_controller_serials() -> list[str]:
    """Fetch connected controller serial numbers, returning [] on failure."""
    try:
        from autopage.api_client import StreamControllerClient
        client = StreamControllerClient()
        serials = client.get_controllers()
        log.info("Found %d controller(s): %s", len(serials), serials)
        return serials
    except Exception as exc:
        log.warning("Could not fetch controllers from StreamController: %s", exc)
        return []


# ── Public API ───────────────────────────────────────────────────────


def toml_to_jsonpage(path: str | Path) -> tuple[str, str]:
    """Convert an ap.toml file to StreamController page JSON.

    1. Parse the TOML definition.
    2. Resolve icon patterns against StreamController icon packs.
    3. Generate StreamController page JSON.

    Returns a tuple of (page_name, page_json).
    """
    path = Path(path)
    log.info("Loading autopage definition from %s", path)

    definition = parse_toml_file(path)

    # Resolve icon regex patterns to real media paths
    _resolve_icons(definition)

    # Fetch connected deck serial numbers for auto-change
    decks = _get_controller_serials()

    page = generate_page_json(definition, decks=decks)
    page_json = page_json_to_string(page)

    # Derive a page name from the filename (strip .ap.toml suffix)
    page_name = path.stem
    if page_name.endswith(".ap"):
        page_name = page_name[: -len(".ap")]

    log.info("Generated page %r with %d button(s)", page_name, len(definition.buttons))

    return page_name, page_json


def push_jsonpage(page_name: str, page_json: str, *, force: bool = False) -> None:
    """Push a JSON page definition to StreamController via DBus API.

    Args:
        page_name: Name of the page to create.
        page_json: JSON string containing the page definition.
        force: If *True* and the page already exists, remove it first
               then re-add.  Without this flag a pre-existing page is
               treated as an error.
    """
    from autopage.api_client import StreamControllerClient

    client = StreamControllerClient()
    try:
        client.add_page(page_name, page_json)
    except Exception as exc:
        if force and "PageExists" in str(exc):
            log.info("Page %r already exists, replacing (--force)", page_name)
            client.remove_page(page_name)
            client.add_page(page_name, page_json)
        else:
            raise
    log.info("Page %r pushed to StreamController", page_name)


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


def process_all_repos(
    *, dev: bool = False, dry_run: bool = False, force: bool = False
) -> None:
    """Discover all ap.toml repos via toml-repo and process each one.

    This is the main entry-point used when no explicit source file is
    provided on the command line.

    Args:
        dev: If True, use local autopage-recipes instead of remote.
        dry_run: If True, print JSON instead of pushing to StreamController.
        force: If True, replace pages that already exist.
    """
    ap_repos = _discover_ap_repos(dev=dev)

    if not ap_repos:
        log.warning("No repos of kind %r found. Nothing to do.", AP_KIND)
        return

    for i, repo in enumerate(ap_repos, 1):
        log.info("Processing repo %d/%d: %s", i, len(ap_repos), repo.url)
        try:
            page_name, page_json = toml_to_jsonpage(repo.url)
            if dry_run:
                print(page_json)
            else:
                push_jsonpage(page_name, page_json, force=force)
        except Exception as exc:
            log.error("Error processing repo %s: %s", repo.url, exc)
