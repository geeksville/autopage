"""Autopage engine: orchestrates TOML parsing, JSON generation, and API calls."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from autopage.json import generate_page_json, page_json_to_string
from autopage.toml import AutopageDef, parse_toml_file

log = logging.getLogger(__name__)


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
    against the icon basename (without file extension).  The first match wins.
    """
    regex = re.compile(pattern, re.IGNORECASE)

    for pack_id, icon_name in catalog:
        # icon_name may be a bare name ("textsms"), a filename ("textsms.png"),
        # or a path ("icons/textsms.png").  Normalise to the bare name.
        basename = icon_name.rsplit("/", 1)[-1]
        name_no_ext = basename.rsplit(".", 1)[0] if "." in basename else basename

        if regex.search(name_no_ext):
            # Build the full media path expected by StreamController.
            # If the API already returned a full path, use it as-is.
            if icon_name.startswith("data/"):
                return icon_name
            # Otherwise construct: data/icons/<pack_id>/icons/<icon_file>
            icon_file = basename if "." in basename else f"{basename}.png"
            return f"data/icons/{pack_id}/icons/{icon_file}"

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

    for button in buttons_with_icons:
        resolved = _match_icon(button.icon, catalog)
        if resolved:
            log.info("Resolved icon %r → %s", button.icon, resolved)
            button.icon = resolved
        else:
            log.warning("No icon matched pattern %r, dropping...", button.icon)
            button.icon = None


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

    page = generate_page_json(definition)
    page_json = page_json_to_string(page)

    # Derive a page name from the filename (strip .ap.toml suffix)
    page_name = path.stem
    if page_name.endswith(".ap"):
        page_name = page_name[: -len(".ap")]

    log.info("Generated page %r with %d button(s)", page_name, len(definition.buttons))

    return page_name, page_json


def push_jsonpage(page_name: str, page_json: str) -> None:
    """Push a JSON page definition to StreamController via DBus API.

    Args:
        page_name: Name of the page to create.
        page_json: JSON string containing the page definition.
    """
    from autopage.api_client import StreamControllerClient

    client = StreamControllerClient()
    client.add_page(page_name, page_json)
    log.info("Page %r pushed to StreamController", page_name)
