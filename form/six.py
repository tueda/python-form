"""Six-like utilities.

Define a small set of objects that resemble those in the six library
by Benjamin Peterson.
"""

import sys

PY3 = sys.version_info[0] >= 3
PY32 = sys.version_info[0:2] >= (3, 2)

if PY3:
    string_types = (str,)
else:
    string_types = (basestring,)
