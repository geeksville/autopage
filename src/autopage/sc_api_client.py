#!/usr/bin/env python3
"""
StreamController DBus API client.

A command-line tool and reusable client for the StreamController DBus API.
This is the legacy backend, selected with ``autopage --streamcontroller``.

Usage:
    python -m autopage.sc_api_client controllers                 # List controller serials
    python -m autopage.sc_api_client pages                       # List all pages
    python -m autopage.sc_api_client add-page NAME [JSON]         # Add a page
    python -m autopage.sc_api_client remove-page NAME             # Remove a page
    python -m autopage.sc_api_client set-active-page SERIAL NAME  # Set active page
    python -m autopage.sc_api_client notify-foreground NAME CLASS # Notify foreground window
    python -m autopage.sc_api_client icon-packs                   # List icon packs
    python -m autopage.sc_api_client icons PACK_ID                # List icons in a pack
    python -m autopage.sc_api_client get-property [--serial S] P  # Read a property
    python -m autopage.sc_api_client listen                      # Listen for property changes
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from typing import Any

from dasbus.connection import SessionMessageBus
from gi.repository import GLib

from autopage.api_client import ApiClient
from autopage.toml import AutopageDef

log = logging.getLogger(__name__)

SERVICE = "com.core447.StreamController"
OBJECT = "/com/core447/StreamController"
IFACE = "com.core447.StreamController"
CTRL_IFACE = "com.core447.StreamController.Controller"
CTRL_BASE = OBJECT + "/controllers"


def _serial_to_dbus_path(serial: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", serial)


class StreamControllerClient(ApiClient):
    """Client for the StreamController DBus API."""

    def __init__(self):
        self._bus = SessionMessageBus()

    def _root_proxy(self):
        return self._bus.get_proxy(SERVICE, OBJECT)

    def _controller_proxy(self, serial: str):
        path = f"{CTRL_BASE}/{_serial_to_dbus_path(serial)}"
        return self._bus.get_proxy(SERVICE, path)

    # ── ApiClient: rendering ─────────────────────────────────────────

    def render_page(self, definition: AutopageDef, *, decks: list[str] | None = None) -> str:
        """Render to a StreamController page JSON string."""
        from autopage.json import generate_page_json, page_json_to_string

        page = generate_page_json(definition, decks=decks)
        return page_json_to_string(page)

    def artifact_to_text(self, artifact: Any) -> str:
        return str(artifact)

    def resolve_icons(self, definition: AutopageDef) -> None:
        from autopage.engine import _resolve_icons

        _resolve_icons(definition, client=self)

    # ── ApiClient: delivery ──────────────────────────────────────────

    def push_page(
        self,
        page_name: str,
        artifact: Any,
        *,
        force: bool = False,
        known_pages: set[str] | None = None,
    ) -> bool:
        if not force and known_pages is not None and page_name in known_pages:
            log.info("Page %r already on controller, skipping (use --force to replace)", page_name)
            return False

        try:
            self.add_page(page_name, artifact)
        except Exception as exc:
            if force and "PageExists" in str(exc):
                log.info("Page %r already exists, replacing (--force)", page_name)
                self.remove_page(page_name)
                self.add_page(page_name, artifact)
            else:
                raise

        if known_pages is not None:
            known_pages.add(page_name)
        log.info("Page %r pushed to StreamController", page_name)
        return True

    def listen_foreground(self, callback) -> None:
        """Dispatch foreground-window changes to ``callback(name, wm_class)``.

        StreamController exposes the window via two properties; we relay each
        ``ForegroundWindow`` change to the supplied callback.
        """

        def _on_change(object_path, iface, prop, value):
            if prop != "ForegroundWindow" or not value:
                return
            # ForegroundWindow is reported as "name\x1fclass" (name, wm_class).
            parts = str(value).split("\x1f", 1)
            name = parts[0]
            wm_class = parts[1] if len(parts) > 1 else ""
            callback(name, wm_class)

        self.listen(_on_change)

    # ── Top-level operations ─────────────────────────────────────────

    def get_controllers(self) -> list[str]:
        """Return serial numbers of all connected controllers."""
        return list(self._root_proxy().Controllers)

    def get_pages(self) -> list[str]:
        """Return a list of page names."""
        return list(self._root_proxy().Pages)

    def add_page(self, name: str, json_contents: str = "") -> None:
        """Add a new page with the given name and optional JSON contents."""
        self._root_proxy().AddPage(name, json_contents)

    def remove_page(self, name: str) -> None:
        """Remove the page with the given name."""
        self._root_proxy().RemovePage(name)

    def notify_foreground(self, window_name: str, window_class: str) -> None:
        """Notify StreamController of the current foreground window."""
        self._root_proxy().NotifyForegroundWindow(window_name, window_class)

    def get_data_path(self) -> str:
        """Return the base data path used by StreamController."""
        return str(self._root_proxy().DataPath)

    def get_icon_packs(self) -> list[str]:
        """Return a list of icon pack IDs."""
        return list(self._root_proxy().IconPacks)

    def get_icon_names(self, pack_id: str) -> list[str]:
        """Return a list of icon names in the given pack."""
        return list(self._root_proxy().GetIconNames(pack_id))

    def get_property(self, name: str) -> object:
        """Read a top-level property by name."""
        return getattr(self._root_proxy(), name)

    # ── Per-controller operations ────────────────────────────────────

    def set_active_page(self, serial: str, name: str) -> None:
        """Set the active page on the given controller."""
        self._controller_proxy(serial).SetActivePage(name)

    def get_controller_property(self, serial: str, name: str) -> object:
        """Read a property from a specific controller."""
        return getattr(self._controller_proxy(serial), name)

    # ── Listener ─────────────────────────────────────────────────────

    def listen(self, callback=None):
        """
        Listen for PropertiesChanged signals. Blocks until interrupted.

        callback(object_path, interface, property_name, value) is called
        for each change.  If callback is None, changes are printed to stdout.
        """
        connection = self._bus.connection

        def _default_callback(object_path, iface, prop, value):
            prefix = "[root]" if object_path == OBJECT else f"[{object_path}]"
            print(f"{prefix} {iface} {prop} = {value!r}")

        cb = callback or _default_callback

        def on_signal(conn, sender, object_path, iface, signal, params):
            sig_iface, changed, invalidated = params.unpack()
            for prop, value in changed.items():
                cb(object_path, sig_iface, prop, value)
            for prop in invalidated:
                cb(object_path, sig_iface, prop, None)

        # Subscribe on root and all sub-objects
        for path in (OBJECT, None):
            connection.signal_subscribe(
                SERVICE,
                "org.freedesktop.DBus.Properties",
                "PropertiesChanged",
                path,
                None,
                0,
                on_signal,
            )

        print(f"Listening for property changes on {SERVICE} …  (Ctrl+C to stop)")
        loop = GLib.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            print("\nStopped.")


_singleton_client: "StreamControllerClient | None" = None


def get_client() -> "StreamControllerClient":
    """Return a shared singleton StreamControllerClient, creating it lazily."""
    global _singleton_client
    if _singleton_client is None:
        _singleton_client = StreamControllerClient()
    return _singleton_client


# ── CLI ──────────────────────────────────────────────────────────────


def build_parser():
    parser = argparse.ArgumentParser(description="StreamController DBus API client")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("controllers", help="List connected controller serial numbers")
    sub.add_parser("pages", help="List all pages")

    p = sub.add_parser("add-page", help="Add a new page (based on an optional JSON template)")
    p.add_argument("name", help="Page name")
    p.add_argument("json", nargs="?", default="", help="JSON contents (optional)")

    p = sub.add_parser("remove-page", help="Remove a page")
    p.add_argument("name", help="Page name")

    p = sub.add_parser("set-active-page", help="Set the active page on a controller")
    p.add_argument("serial", help="Controller serial number")
    p.add_argument("name", help="Page name")

    p = sub.add_parser(
        "notify-foreground",
        help="Notify foreground window (for testing window title notifications)",
    )
    p.add_argument("window_name", help="Window title")
    p.add_argument("window_class", help="Window WM_CLASS")

    sub.add_parser("icon-packs", help="List icon packs")

    p = sub.add_parser("icons", help="List icons in a pack")
    p.add_argument("pack_id", help="Icon pack ID")

    p = sub.add_parser("get-property", help="Read a DBus property")
    p.add_argument(
        "--serial", "-s", default=None, help="Controller serial (omit for top-level properties)"
    )
    p.add_argument("property_name", help="Property name (Controllers, Pages, ActivePageName, …)")

    sub.add_parser("listen", help="Listen for property change notifications")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = get_client()

    try:
        if args.command == "controllers":
            for s in client.get_controllers():
                print(s)

        elif args.command == "pages":
            pages = client.get_pages()
            if not pages:
                print("No pages found.")
            else:
                for p in pages:
                    print(p)

        elif args.command == "add-page":
            client.add_page(args.name, args.json or "")
            print(f"Added page: {args.name}")

        elif args.command == "remove-page":
            client.remove_page(args.name)
            print(f"Removed page: {args.name}")

        elif args.command == "set-active-page":
            client.set_active_page(args.serial, args.name)
            print(f"Set active page: {args.name}")

        elif args.command == "notify-foreground":
            client.notify_foreground(args.window_name, args.window_class)
            print(
                f"Notified foreground window: name={args.window_name!r} class={args.window_class!r}"
            )

        elif args.command == "icon-packs":
            packs = client.get_icon_packs()
            if not packs:
                print("No icon packs found.")
            else:
                for p in packs:
                    print(p)

        elif args.command == "icons":
            icons = client.get_icon_names(args.pack_id)
            if not icons:
                print(f"No icons found in pack: {args.pack_id}")
            else:
                for icon in icons:
                    print(icon)

        elif args.command == "get-property":
            if args.serial:
                value = client.get_controller_property(args.serial, args.property_name)
            else:
                value = client.get_property(args.property_name)
            print(f"{args.property_name} = {value!r}")

        elif args.command == "listen":
            client.listen()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
