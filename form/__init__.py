"""Provide routines for communicating with FORM.

Example
-------
>>> import form
>>> with form.open() as f:
...     f.write('''
...         AutoDeclare Vector p;
...         Local F = g_(0,p1,...,p4);
...         trace4,0;
...         .sort
...     ''')
...     print(f.read('F'))
4*p1.p2*p3.p4-4*p1.p3*p2.p4+4*p1.p4*p2.p3
"""

if False:
    from typing import Optional, Sequence, Union  # noqa: F401

from .formlink import FormError, FormLink  # noqa: F401


def open(args=None, keep_log=False):
    # type: (Optional[Union[str, Sequence[str]]], Union[bool, int]) -> FormLink
    """Open a connection to FORM and return a link object.

    Open a connection to a new FORM process and return a
    :class:`link object <form.FormLink>`.
    The opened connection should be closed by
    :meth:`close() <form.FormLink.close>` of the returned object, which is
    automatically done by use of the "with" statement:

    >>> import form
    >>> with form.open() as formlink:
    ...     pass  # use formlink ...

    The optional argument ``args`` is for the FORM command, a string or
    a sequence of strings. For example '/path/to/form' or ['tform', '-w4'].
    By default, the value of the environment variable ``$FORM`` is used if set,
    otherwise 'form' will be used.

    The other argument ``keep_log`` indicates whether the log from FORM is kept
    and used as detailed information when an error occurs. If the value
    is >= 2, it specifies the maximum number of lines for the scrollback.
    The default value is False.

    Note
    ----
    In the current implementation, ``keep_log=True`` may cause a dead lock when
    the listing of the input is enabled and very long input is sent to FORM.
    """
    return FormLink(args, keep_log)
