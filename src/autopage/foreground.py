"""OS-neutral foreground-window source.

A :class:`ForegroundSource` reports the currently focused window as a
:class:`WindowInfo` (id, WM class, title). This is the seam that lets
auto-switch (``autopage --listen``) work without a StreamController DBus
signal: a backend polls a source and reacts to changes.

Today the only implementation is :class:`KdotoolSource` (KDE / KWin on
Wayland or X11, via the ``kdotool`` executable). Future hosts (GNOME,
macOS, Windows) can add their own :class:`ForegroundSource` subclass and
get wired into :func:`get_default_source`.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass

log = logging.getLogger(__name__)

# How long to wait for a single foreground-window query before giving up.
_QUERY_TIMEOUT_S = 5.0


@dataclass(frozen=True)
class WindowInfo:
    """A focused window's identity.

    ``id`` is an opaque, backend-specific handle (e.g. a KWin UUID). ``name``
    is the window title; ``window_class`` is the application/WM class used for
    match rules. ``pid`` is the owning process id, or ``None`` if the source
    couldn't determine it.
    """

    id: str
    window_class: str
    name: str
    pid: int | None


class ForegroundSource(ABC):
    """Abstract source of the current foreground window."""

    @abstractmethod
    def get_active_window(self) -> WindowInfo | None:
        """Return the current foreground window, or ``None`` if unknown.

        Implementations must not raise for the ordinary "no window / query
        failed" case — they return ``None`` so callers can simply idle.
        """


class KdotoolSource(ForegroundSource):
    """Foreground-window source backed by the ``kdotool`` executable (KDE).

    ``kdotool`` chains query subcommands against a selected window and prints
    one line of output per query, in order. We ask for id, class and title::

        $ kdotool getactivewindow getwindowid getwindowclassname \
              getwindowname getwindowpid
        {58057643-494f-43df-89c8-9660f91a8cdf}   # window id
        code                                     # WM class
        Some Window Title                        # window title
        12345                                    # owning process id

    Requires ``kdotool`` on ``PATH`` plus a reachable session bus (see the
    Fedora devcontainer notes); when no window is focused or the query fails,
    :meth:`get_active_window` returns ``None`` rather than raising.
    """

    # The query subcommands, in the order their output lines appear.
    _QUERY = (
        "getactivewindow",
        "getwindowid",
        "getwindowclassname",
        "getwindowname",
        "getwindowpid",
    )

    def __init__(self, executable: str | None = None) -> None:
        resolved = executable or shutil.which("kdotool")
        if not resolved:
            raise FileNotFoundError(
                "kdotool executable not found on PATH. Install it (Fedora: "
                "`dnf install kdotool`) to use foreground-window auto-switch."
            )
        self._exe = resolved

    def get_active_window(self) -> WindowInfo | None:
        try:
            proc = subprocess.run(
                [self._exe, *self._QUERY],
                capture_output=True,
                text=True,
                timeout=_QUERY_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            log.debug("kdotool query failed: %s", exc)
            return None

        if proc.returncode != 0:
            log.debug("kdotool exited %d: %s", proc.returncode, proc.stderr.strip())
            return None

        # One line per query subcommand after the selector. We expect at least
        # id, class and title; fewer means no active window — treat as unknown.
        # The pid (4th line) is best-effort: missing/unparseable → None.
        lines = proc.stdout.splitlines()
        if len(lines) < 3:
            log.debug("kdotool returned too few lines: %r", proc.stdout)
            return None

        win_id, window_class, name = lines[0], lines[1], lines[2]
        pid: int | None = None
        if len(lines) >= 4:
            try:
                pid = int(lines[3].strip())
            except ValueError:
                log.debug("kdotool returned non-integer pid: %r", lines[3])
        return WindowInfo(id=win_id, window_class=window_class, name=name, pid=pid)


def get_default_source() -> ForegroundSource:
    """Return a foreground-window source for this host.

    Today this is always :class:`KdotoolSource`; the selection logic grows
    here as other platforms gain support.
    """
    return KdotoolSource()


__all__ = [
    "WindowInfo",
    "ForegroundSource",
    "KdotoolSource",
    "get_default_source",
]
