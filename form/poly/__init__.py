"""Provide routines for polynomials via FORM.

This module provides a convenient way to handle polynomial arithmetic in
Python. It heavily uses $-variables in FORM, which are stored in RAM, and
a considerable amount of preprocessor instructions with some overheads. Note
that the most powerful features of FORM, i.e., possibly parallelized SIMD
operations on terms in large expressions on disks are not accessible in this
way.

Note
----

FORM 4.2 or later is strongly recommended to avoid several bugs for
$-variables, polynomial arithmetic etc. in earlier versions of FORM.
Still FORM 4.2 is known to have a bug for big $-variables (see also
`vermaseren/form#215 <https://github.com/vermaseren/form/issues/215>`_).

Examples
--------
>>> from form.poly import Polynomial
>>> def legendre_poly(n, x):
...     assert n >= 0
...     if n == 0:
...         return Polynomial(1)
...     elif n == 1:
...         return Polynomial(x)
...     return ((2 * n - 1) * Polynomial(x) * legendre_poly(n - 1, x) -
...             (n - 1) * legendre_poly(n - 2, x)) / n
>>> for n in range(6):
...     print('P_{0}(z) = {1}'.format(n, legendre_poly(n, 'z')))
P_0(z) = 1
P_1(z) = z
P_2(z) = -1/2+3/2*z^2
P_3(z) = -3/2*z+5/2*z^3
P_4(z) = 3/8-15/4*z^2+35/8*z^4
P_5(z) = 15/8*z-35/4*z^3+63/8*z^5

"""

from .poly import Polynomial, gcd, lcm, symbols  # noqa: F401
