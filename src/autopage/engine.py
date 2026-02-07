"""Autopage engine: orchestrates TOML parsing, JSON generation, and API calls."""

from __future__ import annotations

import logging
from pathlib import Path

from autopage.json import generate_page_json, page_json_to_string
from autopage.toml import parse_toml_file

log = logging.getLogger(__name__)


def process_toml_file(path: str | Path, *, dry_run: bool = False) -> str:
    """Process a single ap.toml file end-to-end.

    1. Parse the TOML definition.
    2. Generate StreamController page JSON.
    3. Push the page via the DBus API (unless *dry_run* is True).

    Returns the generated JSON string.
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

    if dry_run:
        log.info("Dry run — skipping API call")
    else:
        from autopage.api_client import StreamControllerClient

        client = StreamControllerClient()
        client.add_page(page_name, page_json)
        log.info("Page %r pushed to StreamController", page_name)

    return page_json
