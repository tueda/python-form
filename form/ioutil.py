"""Routines for I/O."""

import fcntl
import os

if False:
    from typing import IO  # noqa: F401


def set_nonblock(fd):
    # type: (int) -> None
    """Set the given file descriptor to non-blocking mode."""
    fcntl.fcntl(fd,
                fcntl.F_SETFL,
                fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


class PushbackReader(object):
    """Wrapper for streams with push back operations."""

    def __init__(self, raw):
        # type: (IO[str]) -> None
        """Initialize the reader."""
        self._raw = raw
        self._buf = ''

    def close(self):
        # type: () -> None
        """Close the stream."""
        self._raw.close()

    def fileno(self):
        # type: () -> int
        """Return the file descriptor."""
        return self._raw.fileno()

    def read(self):
        # type: () -> str
        """Read data from the stream."""
        s = self._buf + self._raw.read()
        self._buf = ''
        return s

    def unread(self, s):
        # type: (str) -> None
        """Push back a string.

        Push back the given string to the internal buffer, which will be used
        for the next ``read()`` or ``read0()``.
        """
        self._buf = s + self._buf

    def read0(self):
        # type: () -> str
        """Read the pushed-back string.

        Read a string pushed-back by a previous ``unread()``. No call to
        the underlying raw stream's ``read()`` occurs.
        """
        s = self._buf
        self._buf = ''
        return s
