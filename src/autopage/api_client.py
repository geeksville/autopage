"""Backend-neutral client interface and factory.

An :class:`ApiClient` owns both *rendering* (turning a backend-neutral
:class:`~autopage.toml.AutopageDef` into a backend-native page artifact) and
*delivery* (pushing/activating pages on the target). Concrete backends:

* :class:`autopage.sc_api_client.StreamControllerClient` — the original
  StreamController DBus API.
* :class:`autopage.touchy.TouchyApiClient` — talks directly to touchy-pad
  devices (the default).

Use :func:`get_client` to obtain the active client; select the backend with
:func:`set_backend` (wired up from the CLI).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from autopage.toml import AutopageDef

# Backend identifiers understood by :func:`set_backend` / :func:`get_client`.
BACKEND_TOUCHY = "touchy"
BACKEND_STREAMCONTROLLER = "streamcontroller"

_backend: str = BACKEND_TOUCHY
_singleton_client: "ApiClient | None" = None


def set_backend(name: str) -> None:
    """Select the backend used by :func:`get_client`.

    Resets any existing singleton, so call this before the first
    :func:`get_client` call (the client is a lazily-created singleton).
    """
    global _backend, _singleton_client
    if name not in (BACKEND_TOUCHY, BACKEND_STREAMCONTROLLER):
        raise ValueError(f"Unknown backend: {name!r}")
    _backend = name
    _singleton_client = None


def get_client() -> "ApiClient":
    """Return the shared singleton client for the active backend."""
    global _singleton_client
    if _singleton_client is None:
        if _backend == BACKEND_STREAMCONTROLLER:
            from autopage.sc_api_client import StreamControllerClient

            _singleton_client = StreamControllerClient()
        else:
            from autopage.touchy import TouchyApiClient

            _singleton_client = TouchyApiClient()
    return _singleton_client


class ApiClient(ABC):
    """Abstract backend: renders pages and delivers them to a target."""

    # ── Rendering ────────────────────────────────────────────────────

    @abstractmethod
    def render_page(self, definition: "AutopageDef", *, decks: list[str] | None = None) -> Any:
        """Render *definition* into an opaque backend-native page artifact."""

    @abstractmethod
    def artifact_to_text(self, artifact: Any) -> str:
        """Return a human-readable form of *artifact* (for ``--dry-run``)."""

    def resolve_icons(self, definition: "AutopageDef") -> None:
        """Resolve button icon hints in-place. Default: no-op."""
        return None

    # ── Delivery ─────────────────────────────────────────────────────

    @abstractmethod
    def push_page(
        self,
        page_name: str,
        artifact: Any,
        *,
        force: bool = False,
        known_pages: set[str] | None = None,
    ) -> bool:
        """Push a rendered page. Returns True if pushed, False if skipped."""

    @abstractmethod
    def get_controllers(self) -> list[str]:
        """Return serial numbers / ids of connected target devices."""

    @abstractmethod
    def get_pages(self) -> list[str]:
        """Return the names of pages already present on the target."""

    @abstractmethod
    def set_active_page(self, serial: str, name: str) -> None:
        """Activate the named page on the given device."""

    # ── Foreground-window listener ───────────────────────────────────

    def listen_foreground(self, callback) -> None:
        """Listen for foreground-window changes and dispatch to *callback*.

        ``callback(window_name, window_class)`` is invoked on each change.
        Backends without a window source raise :class:`NotImplementedError`.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support foreground-window listening"
        )
