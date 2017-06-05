"""Provide routines for polynomials via FORM.

This module provides a convenient way to handle polynomial arithmetic in
Python. It heavily uses $-variables in FORM, which are stored in RAM. Note that
the most powerful features of FORM, i.e., (possibly parallelized) operations
on large expressions on disks are not accessible in this way.
"""

from .poly import Polynomial, gcd, lcm  # noqa: F401
