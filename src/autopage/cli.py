"""Command-line interface for autopage."""

import argparse
import logging
import sys

from autopage.engine import (
    listen_and_autoswitch,
    process_all_repos,
    push_jsonpage,
    toml_to_jsonpage,
)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the autopage CLI."""
    parser = argparse.ArgumentParser(
        prog="autopage",
        description="Automatic StreamController page definitions from TOML configs.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and generate JSON without pushing to StreamController",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Replace the page if it already exists (remove then re-add)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Use local autopage-recipes directory instead of remote GitHub repo",
    )
    parser.add_argument(
        "--listen",
        action="store_true",
        help="Listen for foreground window changes and auto-switch pages based on match rules",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path or URL to an ap.toml file. If omitted, uses toml-repo to discover all ap.toml files.",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        if args.listen:
            # Listen mode: watch for foreground window changes, auto-push matching pages
            listen_and_autoswitch(dev=args.dev, force=args.force)
        elif args.source is not None:
            # Single-file mode
            page_name, page_json = toml_to_jsonpage(args.source)
            if args.dry_run:
                print(page_json)
            else:
                push_jsonpage(page_name, page_json, force=args.force)
        else:
            # Discovery mode: use toml-repo to find all ap.toml files
            process_all_repos(dev=args.dev, dry_run=args.dry_run, force=args.force)
    except Exception as exc:
        logging.error("%s", exc)
        return 1

    return 0


def _get_version() -> str:
    from autopage import __version__

    return __version__


if __name__ == "__main__":
    sys.exit(main())
