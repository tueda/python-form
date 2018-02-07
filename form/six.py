"""Six-like utilities.

Define a small set of objects that resemble those in the six library
by Benjamin Peterson.
"""

import sys

if sys.version_info[0] >= 3:
    string_types = (str,)
else:
    string_types = (basestring,)  # noqa: F821
