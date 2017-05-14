"""Routines for I/O."""

import fcntl
import os


def set_nonblock(fd):
    """Set the given file descriptor to non-blocking mode."""
    fcntl.fcntl(fd,
                fcntl.F_SETFL,
                fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


class PushbackReader(object):
    """Wrapper for streams with push back operations."""

    def __init__(self, raw):
        """Initialize the reader."""
        self._raw = raw
        self._buf = ''

    def close(self):
        """Close the stream."""
        self._raw.close()

    def fileno(self):
        """Return the file descriptor."""
        return self._raw.fileno()

    def read(self):
        """Read data from the stream."""
        s = self._buf + self._raw.read()
        self._buf = ''
        return s

    def unread(self, s):
        """Push back a string.

        Push back the given string to the internal buffer, which will be used
        for the next `read()` or `read0()`.
        """
        self._buf = s + self._buf

    def read0(self):
        """Read the pushed-back string.

        Read a string pushed-back by a previous `unread()'. No call to
        the underlying raw stream's `read()` occurs.
        """
        s = self._buf
        self._buf = ''
        return s
