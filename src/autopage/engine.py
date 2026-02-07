"""Autopage engine: orchestrates TOML parsing, JSON generation, and API calls."""

from __future__ import annotations

import logging
from pathlib import Path

from autopage.json import generate_page_json, page_json_to_string
from autopage.toml import parse_toml_file

log = logging.getLogger(__name__)


def toml_to_jsonpage(path: str | Path) -> tuple[str, str]:
    """Convert an ap.toml file to StreamController page JSON.

    1. Parse the TOML definition.
    2. Generate StreamController page JSON.

    Returns a tuple of (page_name, page_json).
    """
    path = Path(path)
    log.info("Loading autopage definition from %s", path)

    definition = parse_toml_file(path)
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
