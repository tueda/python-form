"""Provide routines for polynomials via FORM.

This module provides a convenient way to handle polynomial arithmetic in
Python. It heavily uses $-variables in FORM, which are stored in RAM, and
a considerable amount of preprocessor instructions with some overheads. Note
that the most powerful features of FORM, i.e., possibly parallelized SIMD
operations on terms in large expressions on disks are not accessible in this
way.
"""

from .poly import Polynomial, gcd, lcm, symbols  # noqa: F401
