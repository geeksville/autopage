"""Command-line interface for autopage."""

import argparse
import logging
import sys


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
        "source",
        nargs="?",
        help="Path or URL to an ap.toml file or toml-repo directory",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.source is None:
        parser.print_help()
        return 1

    from autopage.engine import push_jsonpage, toml_to_jsonpage

    try:
        page_name, page_json = toml_to_jsonpage(args.source)
        if args.dry_run:
            print(page_json)
        else:
            push_jsonpage(page_name, page_json, force=args.force)
    except Exception as exc:
        logging.error("%s", exc)
        return 1

    return 0


def _get_version() -> str:
    from autopage import __version__

    return __version__


if __name__ == "__main__":
    sys.exit(main())
