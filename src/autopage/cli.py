"""Command-line interface for autopage."""

import argparse
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
        "source",
        nargs="?",
        help="Path or URL to an ap.toml file or toml-repo directory",
    )

    args = parser.parse_args(argv)

    if args.source is None:
        parser.print_help()
        return 1

    # TODO: implement page loading logic
    print(f"Loading autopage definitions from: {args.source}")
    return 0


def _get_version() -> str:
    from autopage import __version__

    return __version__


if __name__ == "__main__":
    sys.exit(main())
