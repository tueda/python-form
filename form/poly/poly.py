"""Routines for polynomials via FORM."""

from fractions import Fraction

from . import singleton
from .parser import (is_bracketed_symbol, is_expression, is_lhs, is_symbol,
                     split_symbols, split_terms)
from ..six import integer_types, string_types


class Polynomial(object):
    """Polynomial.

    An immutable multivariate polynomial object with rational number
    coefficients stored in the expanded form as a $-variable in FORM.
    Many standard operators (i.e., ``+``, ``-``, ``*``) are supported.

    Some methods have an option ``check``, which is ``True`` in default and
    enables checking of the validity of the input.

    Examples
    --------
    Create polynomials. All identifiers (matching to the regular expression
    ``[a-zA-Z][0-9a-zA-Z]*``) are recognized as symbols:

    >>> Polynomial(5)
    Polynomial('5')
    >>> Polynomial('x')
    Polynomial('x')
    >>> Polynomial('(1+x)*(1-x)')
    Polynomial('1-x^2')

    Addition, subtraction and multiplication:

    >>> p = Polynomial('x+y')
    >>> q = Polynomial('x-y')
    >>> +p
    Polynomial('y+x')
    >>> -p
    Polynomial('-y-x')
    >>> p + q
    Polynomial('2*x')
    >>> p - q
    Polynomial('2*y')
    >>> p * q
    Polynomial('-y^2+x^2')
    >>> 2 * (1 + p) - 3 * (1 - q)
    Polynomial('-1-y+5*x')

    Exponentiation with a non-negative integer exponent:

    >>> p = Polynomial('1+x')
    >>> p ** 3
    Polynomial('1+3*x+3*x^2+x^3')

    ``len()`` gives the number of terms in the expanded form:

    >>> p = Polynomial('(1+x)^4')
    >>> p
    Polynomial('1+4*x+6*x^2+4*x^3+x^4')
    >>> len(p)
    5

    A polynomial as a collection of terms:

    >>> p = Polynomial('1+2*x+x^2')
    >>> [t for t in p]
    [Polynomial('1'), Polynomial('2*x'), Polynomial('x^2')]

    Equality operators:

    >>> p = Polynomial('1+x')
    >>> q = Polynomial('1-x')
    >>> p == q
    False
    >>> p != q
    True
    >>> p + q == 2
    True

    Polynomial division:

    >>> f = Polynomial('x^2')
    >>> g = Polynomial('2*x + a')
    >>> q = f // g
    >>> r = f % g
    >>> q
    Polynomial('-1/4*a+1/2*x')
    >>> r
    Polynomial('1/4*a^2')
    >>> f == q * g + r
    True

    Exact division (for a single-term divisor):

    >>> p = Polynomial('2-x^2')
    >>> x = Polynomial('2*x')
    >>> p / 2
    Polynomial('1-1/2*x^2')
    >>> p / x
    Polynomial('x^-1-1/2*x')

    """

    _form = None  # The singleton.
    _have_gcd0 = False  # correct gcd_(0,a)
    _have_mul = False  # mul_ function

    @classmethod
    def get_instance(cls):
        """Return the FORM instance for polynomial arithmetic."""
        if cls._form is None:
            cls._form = singleton.FormSingleton()
            # Implicit declaration for symbols.
            cls._form.install_hook(
                'Auto S '
                'a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,'
                'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z;'
                'Auto CF PythonFormPRIVATEf;'
            )
            # Check FORM features/bugs.

            def h(f):
                # gcd(0,a): FORM 4.1 (Jun  8 2017, v4.1-20131025-352-g7cf7c42)
                cls._have_gcd0 = f._dateversion > 20170608
                # mul_: FORM 4.1 (Jun 10 2017, v4.1-20131025-355-g0bf5c58)
                cls._have_mul = f._dateversion >= 20170610

            cls._form.install_hook(h)
        return cls._form

    def __init__(self, expr=0, check=True):
        """Construct a polynomial.

        Examples
        --------
        >>> Polynomial(12)
        Polynomial('12')
        >>> Polynomial('1+x')
        Polynomial('1+x')
        >>> p = Polynomial('1+y')
        >>> Polynomial(p)
        Polynomial('1+y')

        """
        self.get_instance()  # Ensure self._form
        if isinstance(expr, Polynomial):
            self._id = self._form.next_id()
            self._str = expr._str
            self._len = expr._len
            self._form.write('#{0}={1};'.format(self._id, expr._id))
        elif isinstance(expr, string_types):
            if check and not is_expression(expr):
                raise ValueError(
                    'Illegal polynomial input: {0}'.format(repr(expr)))
            self._id = self._form.next_id()
            self._str = None
            self._len = None
            self._form.write('#{0}={1};'.format(self._id, expr))
            if check:
                self._form.write((
                    '#$t=0;\n'
                    '#inside {0}\n'
                    'if(match(PythonFormPRIVATEf?(?a)))$t=1;\n'
                    '#endinside'
                ).format(self._id))
                if int(self._form.read('$t')):
                    raise ValueError(
                        'Illegal polynomial input: {0}'.format(repr(expr)))
        elif isinstance(expr, (integer_types, Fraction)):
            self._id = self._form.next_id()
            self._str = None
            self._len = None
            self._form.write('#{0}={1};'.format(self._id, expr))
        else:
            raise TypeError('Illegal polynomial input: {0}'.format(repr(expr)))
        # self._form.check()

    def __del__(self):
        """Destructor."""
        if self._form.closed:
            return
        # Ignore possible errors caused by subtle timing problems.
        try:
            self._form.write('#{0}=0;'.format(self._id))
            self._form.free_id(self._id)
        except AttributeError:
            pass

    def __copy__(self):
        """Return a shallow copy of the polynomial."""
        return self

    def __deepcopy__(self, memo):
        """Return a deep copy of the polynomial."""
        return Polynomial(self, False)

    def __getstate__(self):
        """Return the state object of the polynomial."""
        # FORM connections can't be pickled. Instead, pickle the string
        # representation of the polynomial.
        return {'s': str(self)}

    def __setstate__(self, state):
        """Set the state object to the polynomial."""
        self.get_instance()  # Ensure self._form
        self._id = self._form.next_id()
        # self._str = state['s']
        self._str = None  # To be determined: the term order may be different.
        self._len = None
        self._form.write('#{0}={1};'.format(self._id, state['s']))
        # self._form.check()

    def _clear_cache(self):
        """Clear cached statuses."""
        self._str = None
        self._len = None

    def __str__(self):
        """Informal string representation."""
        if self._str is None:
            self._str = self._form.read(self._id)
        return self._str

    def __repr__(self):
        """Formal string representation."""
        return "Polynomial('{0}')".format(str(self))

    def __hash__(self):
        """Hash value."""
        return hash(str(self))

    def __len__(self):
        """Return the number of terms.

        Examples
        --------
        >>> len(Polynomial(0))
        0
        >>> len(Polynomial(-12))
        1
        >>> len(Polynomial('x'))
        1
        >>> len(Polynomial('1+x+y') ** 3)
        10

        """
        if self._len is None:
            self._form.write('#$t=termsin_({0});'.format(self._id))
            self._len = int(self._form.read('$t'))
        return self._len

    def __iter__(self):
        """Return an iterator for all terms in the polynomial."""
        if self:
            for t in split_terms(str(self)):
                yield Polynomial(t, False)

    @property
    def is_zero(self):
        """Return True if the polynomial is zero."""
        return len(self) == 0

    @property
    def is_one(self):
        """Return True if the polynomial is one."""
        return len(self) == 1 and str(self) == '1'

    @property
    def is_integer(self):
        """Return True if the polynomial is an integer."""
        try:
            self.integer
            return True
        except ValueError:
            return False

    @property
    def is_number(self):
        """Return True if the polynomial is a rational number."""
        try:
            self.fraction
            return True
        except ValueError:
            return False

    @property
    def is_symbol(self):
        """Return True if the polynomial is a symbol."""
        return (len(self) == 1 and
                (is_symbol(str(self)) or is_bracketed_symbol(str(self))))

    @property
    def unit(self):
        """Return the unit of the polynomial (the sign of the first term)."""
        self._form.write((
            '#if termsin({0})\n'
            '#$t1=firstterm_({0});\n'
            '#inside $t1\n'
            '$t=coeff_;\n'
            '#endinside\n'
            '#$t=sig_($t);\n'
            '#else\n'
            '#$t=0;\n'
            '#endif'
        ).format(self._id))
        return int(self._form.read('$t'))

    @property
    def integer(self):
        """Convert the polynomial into an integer."""
        return int(str(self))

    @property
    def fraction(self):
        """Convert the polynomial into a fraction."""
        try:
            return Fraction(self.integer)
        except ValueError:
            pass
        a = str(self).split('/', 1)
        if len(a) != 2:
            raise ValueError('{0} is not a fraction'.format(self))
        return Fraction(int(a[0]), int(a[1]))

    def __eq__(self, other):
        """Return self == other.

        Examples
        --------
        >>> x = Polynomial('x')
        >>> u = Polynomial('1')
        >>> p = 1 + x
        >>> q = 1 - x

        >>> p == u
        False
        >>> p == 2 - q
        True
        >>> p == 0
        False
        >>> p == 1
        False
        >>> u == 1
        True

        """
        if isinstance(other, Polynomial):
            if len(self) != len(other):
                return False
            if self._str is not None and other._str is not None:
                # When the string representations of the both are known,
                # make use of them.
                return self._str == other._str
            self._form.write('#$t={0}-{1};\n#$t=nterms_($t);'.format(
                self._id, other._id))
            return self._form.read('$t') == '0'
        if isinstance(other, integer_types):
            if other == 0:
                return len(self) == 0
            if len(self) != 1:
                return False
            self._form.write('#$t={0}-{1};\n#$t=nterms_($t);'.format(
                self._id, other))
            return self._form.read('$t') == '0'
        raise TypeError('polynomial expected: {0}'.format(repr(other)))

    def __ne__(self, other):
        """Return self != other.

        Examples
        --------
        >>> x = Polynomial('x')
        >>> y = Polynomial('y')

        >>> x != y
        True

        """
        return not (self == other)

    def __pos__(self):
        """Return + self.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> + p
        Polynomial('1+x')

        """
        return self

    def __neg__(self):
        """Return - self.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> - p
        Polynomial('-1-x')

        """
        return Polynomial('-{0}'.format(self._id), False)

    def __add__(self, other):
        """Return self + other.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> q = Polynomial('1-x')
        >>> p + q
        Polynomial('2')
        >>> p + 1
        Polynomial('2+x')

        """
        if isinstance(other, Polynomial):
            return Polynomial('{0}+{1}'.format(self._id, other._id), False)
        if isinstance(other, integer_types):
            return Polynomial('{0}+{1}'.format(self._id, other), False)
        return NotImplemented

    def __radd__(self, other):
        """Return other + self.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> 1 + p
        Polynomial('2+x')

        """
        return self.__add__(other)

    def __sub__(self, other):
        """Return self - other.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> q = Polynomial('1-x')
        >>> p - q
        Polynomial('2*x')
        >>> p - 1
        Polynomial('x')

        """
        if isinstance(other, Polynomial):
            return Polynomial('{0}-{1}'.format(self._id, other._id), False)
        if isinstance(other, integer_types):
            return Polynomial('{0}-{1}'.format(self._id, other), False)
        return NotImplemented

    def __rsub__(self, other):
        """Return other - self.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> 1 - p
        Polynomial('-x')

        """
        if isinstance(other, integer_types):
            return Polynomial('{0}-{1}'.format(other, self._id), False)
        return NotImplemented

    def __mul__(self, other):
        """Return self * other.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> q = Polynomial('1-x')
        >>> p * q
        Polynomial('1-x^2')
        >>> p * 2
        Polynomial('2+2*x')

        """
        if isinstance(other, Polynomial):
            return Polynomial((
                'mul_({0},{1})' if self._have_mul else '{0}*{1}'
            ).format(self._id, other._id), False)
        if isinstance(other, integer_types):
            return Polynomial('{0}*{1}'.format(self._id, other), False)
        return NotImplemented

    def __rmul__(self, other):
        """Return other * self.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> 2 * p
        Polynomial('2+2*x')

        """
        return self.__mul__(other)

    def __pow__(self, other):
        """Return self ** other.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> p ** 2
        Polynomial('1+2*x+x^2')

        """
        if isinstance(other, integer_types) and other >= 0:
            return Polynomial('{0}^{1}'.format(self._id, other), False)
        return NotImplemented

    def __floordiv__(self, other):
        """Return self // other.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> q = Polynomial('1-x')
        >>> p // q
        Polynomial('-1')
        >>> p // 2
        Polynomial('1/2+1/2*x')

        """
        if isinstance(other, Polynomial):
            return Polynomial('div_({0},{1})'.format(self._id, other._id),
                              False)
        if isinstance(other, integer_types):
            if other == 0:
                raise ZeroDivisionError('polynomial division by zero')
            return Polynomial('div_({0},{1})'.format(self._id, other), False)
        return NotImplemented

    def __rfloordiv__(self, other):
        """Return other // self.

        Examples
        --------
        >>> p = Polynomial('1-x')
        >>> 1 // p
        Polynomial('0')

        """
        if isinstance(other, integer_types):
            return Polynomial('div_({0},{1})'.format(other, self._id), False)
        return NotImplemented

    def __mod__(self, other):
        """Return self % other.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> q = Polynomial('1-x')
        >>> p % q
        Polynomial('2')
        >>> p % 2
        Polynomial('0')

        """
        if isinstance(other, Polynomial):
            return Polynomial('rem_({0},{1})'.format(self._id, other._id),
                              False)
        if isinstance(other, integer_types):
            if other == 0:
                raise ZeroDivisionError('polynomial remainder by zero')
            return Polynomial('rem_({0},{1})'.format(self._id, other), False)
        return NotImplemented

    def __rmod__(self, other):
        """Return other % self.

        Examples
        --------
        >>> p = Polynomial('1-x')
        >>> 1 % p
        Polynomial('1')

        """
        if isinstance(other, integer_types):
            return Polynomial('rem_({0},{1})'.format(other, self._id), False)
        return NotImplemented

    def __truediv__(self, other):
        """Return self / other.

        Examples
        --------
        >>> p = Polynomial('x+x^2')
        >>> q = Polynomial('x')
        >>> p / q
        Polynomial('1+x')
        >>> p / 2
        Polynomial('1/2*x+1/2*x^2')

        """
        if isinstance(other, Polynomial):
            if len(other) == 0:
                raise ZeroDivisionError('polynomial division by zero')
            if len(other) != 1:
                return NotImplemented
            return Polynomial('{0}/{1}'.format(self._id, other._id), False)
        if isinstance(other, integer_types):
            if other == 0:
                raise ZeroDivisionError('polynomial division by zero')
            return Polynomial('{0}/{1}'.format(self._id, other), False)
        return NotImplemented

    def __rtruediv__(self, other):
        """Return other / self.

        Examples
        --------
        >>> x = Polynomial('x')
        >>> 2 / x
        Polynomial('2*x^-1')

        """
        if isinstance(other, integer_types):
            if len(self) == 0:
                raise ZeroDivisionError('polynomial division by zero')
            if len(self) != 1:
                return NotImplemented
            return Polynomial('{0}/{1}'.format(other, self._id), False)
        return NotImplemented

    # For Python 2.x.
    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    @staticmethod
    def _interpret_symbols(x, check=True):
        """Try to interpret ``x`` as symbols and return a list of strings."""
        if isinstance(x, string_types):
            a = split_symbols(x, True)
            if not a:
                raise ValueError('symbol(s) expected: {0}'.format(x))
            return a
        if isinstance(x, Polynomial):
            if check and not x.is_symbol:
                raise ValueError('symbol expected: {0}'.format(
                    repr(x)))
            return ["`{0}'".format(x._id)]
        if isinstance(x, (tuple, list, set, frozenset)):
            if not x:
                raise ValueError('symbol(s) expected: {0}'.format(x))

            def _check(x):
                if isinstance(x, string_types):
                    if check and not is_symbol(x):
                        raise ValueError('symbol expected: {0}'.format(
                            repr(x)))
                    return x
                if isinstance(x, Polynomial):
                    if check and not x.is_symbol:
                        raise ValueError('symbol expected: {0}'.format(
                            repr(x)))
                    return "`{0}'".format(x._id)
                raise TypeError('symbol expected: {0}'.format(repr(x)))

            return [_check(y) for y in x]
        raise TypeError('symbol(s) expected: {0}'.format(repr(x)))

    def factorize(self):
        """Return a generator iterating factors of the polynomial.

        Examples
        --------
        >>> p = Polynomial('x^3 - y^3')
        >>> sorted(p.factorize(), key=lambda x: (len(x), str(x)))
        [Polynomial('-1'), Polynomial('y-x'), Polynomial('y^2+x*y+x^2')]

        Note
        ----

        The order of factors in the result depends on the implementation of
        FORM. The user may need to sort the result in some adequate order.

        """
        self._form.write('#factdollar {0}'.format(self._id))

        def factorization_generator():
            self._form.write('#$t={0}[0];'.format(self._id))
            n = int(self._form.read('$t'))
            for i in range(n):
                yield Polynomial('{0}[{1}]'.format(self._id, i + 1), False)

        return factorization_generator()

    def degree(self, x, w=None, f=max, check=True):
        """Return the degree with respect to ``x``.

        Return the degree of the polynomial with respect to ``x``, which must
        be a symbol or symbols. The optional argument ``w`` gives integer
        weights, which are ``1`` in default. Another optional argument ``f``
        specifies a function to manipulate the set of exponents:

        ======== =============================
          f        meaning
        ======== =============================
          max      the maximum power (default)
          min      the minimum power
          list     all powers as a list
          set      powers as a set
        ======== =============================

        Examples
        --------
        >>> p = Polynomial('a*x + b*x + c*x^3 + d*x^6')
        >>> p.degree('x')
        6
        >>> p.degree('x', f=min)
        1
        >>> p.degree('x', f=list) == [1, 1, 3, 6]
        True
        >>> p.degree('x', f=set) == set([1, 3, 6])
        True

        When a list of symbols is given, the total degree is considered.

        >>> p = Polynomial('1+x+y+z') ** 2
        >>> p
        Polynomial('1+2*z+z^2+2*y+2*y*z+y^2+2*x+2*x*z+2*x*y+x^2')
        >>> p.degree(['x', 'y'], f=list)
        [0, 0, 0, 1, 1, 2, 1, 1, 2, 2]

        Degrees with the weight option:

        >>> p = Polynomial('x^2*y^5')
        >>> p.degree(['x', 'y'])
        7
        >>> p.degree(['x', 'y'], w=[1, 2])
        12
        >>> p.degree(['x', 'y'], w=[1, -1])
        -3

        """
        x = self._interpret_symbols(x, check)

        if w is None:
            count_args = ','.join('{0},1'.format(y) for y in x)
        else:
            if isinstance(w, integer_types):
                w = (w,)
            elif (not isinstance(w, (tuple, list)) or
                    any(not isinstance(y, integer_types) for y in w)):
                raise TypeError('integer weight(s) expected: {0}'.format(
                    repr(w)))
            if len(x) != len(w):
                raise ValueError((
                    'number of symbols and that of weights mismatch: '
                    '{0}, {1}').format(repr(x), repr(w)))
            count_args = ','.join('{0},{1}'.format(y, z) for y, z in zip(x, w))

        if f is max:
            # XXX: the minimum power assumed.
            self._form.write((
                '#$t=-32768;\n'
                '#inside {0}\n'
                'if(count({1})>$t)$t=count_({1});\n'
                '#endinside'
            ).format(self._id, count_args))
            n = int(self._form.read('$t'))
            if n == -32768:
                n = 0
            return n
        if f is min:
            # XXX: the maximum power assumed.
            self._form.write((
                '#$t=32767;\n'
                '#inside {0}\n'
                'if(count({1})<$t)$t=count_({1});\n'
                '#endinside'
            ).format(self._id, count_args))
            n = int(self._form.read('$t'))
            if n == 32767:
                n = 0
            return n
        if f is list:
            # XXX: intended for small polynomials.
            self._form.write((
                '#$t=dum_();\n'
                '#inside {0}\n'
                '$t1=count_({1});\n'
                'inside $t;\n'
                'id dum_(?a)=dum_(?a,$t1);\n'
                'endinside;\n'
                '#endinside'
            ).format(self._id, count_args))
            s = self._form.read('$t')[1:-1]
            if not s:
                return []
            return [int(i) for i in s.split(',')]
        if f is set:
            return set(self.degree(x, w, list, False))
        raise ValueError('invalid degree specification: {0}'.format(repr(f)))

    def coefficient(self, x, n, check=True):
        """Return the coefficient of ``x^n``.

        Return the coefficient of ``x^n`` in the polynomial, where ``x`` must
        be a symbol and ``n`` is an integer.

        Examples
        --------
        >>> p = Polynomial('1+x+y') ** 3
        >>> p.coefficient('x', 1)
        Polynomial('3+6*y+3*y^2')
        >>> p.coefficient('y', 2)
        Polynomial('3+3*x')

        """
        if isinstance(x, string_types):
            if check and not is_symbol(x):
                raise ValueError('symbol expected: {0}'.format(repr(x)))
        elif isinstance(x, Polynomial):
            if check:
                if not x.is_symbol:
                    raise ValueError('symbol expected: {0}'.format(repr(x)))
                x = str(x)
            else:
                x = "`{0}'".format(x._id)
        else:
            raise TypeError('symbol expected: {0}'.format(repr(x)))

        if not isinstance(n, integer_types):
            raise TypeError('integer expected: {0}'.format(repr(n)))

        p = Polynomial(self, False)
        self._form.write((
            '#inside {0}\n'
            'if(count({1},1)!={2})discard;\n'
            'multiply 1/{1}^{2};\n'
            '#endinside'
        ).format(p._id, x, n))
        p._clear_cache()
        return p

    def diff(self, x, n=1, check=True):
        """Return the derivative with respect to ``x``.

        Return the ``n``-th derivative of the polynomial with respect to ``x``,
        where ``x`` must be a symbol and ``n`` is a non-negative integer.

        Examples
        --------
        >>> p = Polynomial('1+x+y') ** 3
        >>> p.diff('x')
        Polynomial('3+6*y+3*y^2+6*x+6*x*y+3*x^2')

        """
        if isinstance(x, string_types):
            if check and not is_symbol(x):
                raise ValueError('symbol expected: {0}'.format(repr(x)))
        elif isinstance(x, Polynomial):
            if check:
                if not x.is_symbol:
                    raise ValueError('symbol expected: {0}'.format(repr(x)))
                x = str(x)
            else:
                x = "`{0}'".format(x._id)
        else:
            raise TypeError('symbol expected: {0}'.format(repr(x)))

        if not isinstance(n, integer_types):
            raise TypeError('non-negative integer expected: {0}'.format(
                repr(n)))
        if n < 0:
            raise TypeError('non-negative integer expected: {0}'.format(
                repr(n)))

        if n == 0:
            return self

        p = Polynomial(self, False)
        if n == 1:
            self._form.write((
                '#inside {0}\n'
                'id {1}^PythonFormPRIVATEn?'
                '=PythonFormPRIVATEn*{1}^PythonFormPRIVATEn/{1};\n'
                '#endinside'
            ).format(p._id, x))
        else:
            self._form.write((
                '#do i=1,{2}\n'
                '#inside {0}\n'
                'id {1}^PythonFormPRIVATEn?'
                '=PythonFormPRIVATEn*{1}^PythonFormPRIVATEn/{1};\n'
                '#endinside\n'
                '#enddo'
            ).format(p._id, x, n))
        p._clear_cache()
        return p

    def subs(self, lhs, rhs, check=True):
        """Return the result of an algebraic replacement.

        Apply the algebraic replacement ``lhs = rhs`` and return the result.
        ``lhs`` must consist of products of symbols.

        Examples
        --------
        >>> p = Polynomial('x + x*y + y^2')
        >>> p.subs('x', 'y')
        Polynomial('y+2*y^2')
        >>> p.subs('x*y', '1 + z')
        Polynomial('1+z+y^2+x')

        """
        if isinstance(lhs, string_types):
            if check and not is_lhs(lhs):
                raise ValueError('lhs expected: {0}'.format(repr(lhs)))
        elif isinstance(lhs, Polynomial):
            if check:
                if len(lhs) != 1 or not is_lhs(str(lhs)):
                    raise ValueError('lhs expected: {0}'.format(repr(lhs)))
        else:
            raise TypeError('lhs expected: {0}'.format(repr(lhs)))

        if isinstance(rhs, string_types):
            if check:
                p = Polynomial(rhs, True)
        elif isinstance(rhs, (Polynomial, integer_types)):
            pass
        else:
            raise TypeError('rhs expected: {0}'.format(repr(rhs)))

        p = Polynomial(self, False)
        self._form.write((
            '#inside {0}\n'
            'id {1}={2};\n'
            '#endinside'
        ).format(
            p._id,
            "`{0}'".format(lhs._id) if isinstance(lhs, Polynomial) else lhs,
            rhs._id if isinstance(rhs, Polynomial) else rhs
        ))
        p._clear_cache()
        return p


def symbols(names, seq=False):
    """Translate a string to symbols and return them as polynomials.

    Examples
    --------
    The ``names`` argument can be a string with commas or whitespaces as
    delimiters.

    >>> symbols('x,y,z')
    [Polynomial('x'), Polynomial('y'), Polynomial('z')]
    >>> symbols('a b c')
    [Polynomial('a'), Polynomial('b'), Polynomial('c')]

    >>> symbols('x')
    Polynomial('x')
    >>> symbols('x,y')
    [Polynomial('x'), Polynomial('y')]
    >>> symbols('x,y,z')
    [Polynomial('x'), Polynomial('y'), Polynomial('z')]

    A trailing ``,`` or setting ``seq=True`` guarantees that the return value
    is a list.

    >>> symbols('x,')
    [Polynomial('x')]
    >>> symbols('x', seq=True)
    [Polynomial('x')]

    Triple dot operators ``...`` are expanded for symbols containing
    non-negative numbers unless ambiguous.

    >>> symbols('x1,...,x3')
    [Polynomial('x1'), Polynomial('x2'), Polynomial('x3')]
    >>> symbols('x1y11z2...x3y9z2')
    [Polynomial('x1y11z2'), Polynomial('x2y10z2'), Polynomial('x3y9z2')]

    """
    if not isinstance(names, string_types):
        raise TypeError('string expected: {0}'.format(repr(names)))

    a = split_symbols(names, seq)

    if not a:
        raise ValueError('no symbols given')

    if isinstance(a, string_types):
        return Polynomial(a, False)

    return [Polynomial(x, False) for x in a]


def gcd(*polynomials):
    """Return the greatest common divisor of the given polynomials.

    Examples
    --------
    >>> p1 = Polynomial('(1+x)^1*(2+x)^3')
    >>> p2 = Polynomial('(1+x)^2*(2+x)^1')
    >>> gcd(p1, p2)
    Polynomial('2+3*x+x^2')

    """
    if (polynomials and len(polynomials) == 1 and
            isinstance(polynomials[0], (tuple, list, set, frozenset))):
        polynomials = polynomials[0]

    if any(not isinstance(p, (Polynomial, integer_types))
           for p in polynomials):
        raise TypeError('polynomial expected: {0}'.format(', '.join(
            repr(p) for p in polynomials
            if not isinstance(p, (Polynomial, integer_types))
        )))

    if not polynomials:
        raise TypeError('gcd() takes one or more arguments')
    if len(polynomials) == 1:
        # GCD(a) = a.
        if isinstance(polynomials, (set, frozenset)):
            polynomials = tuple(polynomials)
        return (polynomials[0] if isinstance(polynomials[0], Polynomial)
                else Polynomial(polynomials[0], False))

    form = Polynomial.get_instance()

    if Polynomial._have_mul:
        return Polynomial('gcd_({0})'.format(','.join((
            p._id if isinstance(p, Polynomial) else str(p)
        ) for p in polynomials)), False)
    else:
        # Old FORM can't accept 0 for gcd_ (vermaseren/form#191).
        # GCD(a, 0) = GCD(0, a) = a,
        # GCD(0, 0) = 0.
        form.write('#$t=0;')
        for p in polynomials:
            if isinstance(p, Polynomial):
                form.write((
                    '#if termsin($t)\n'
                    '#if termsin({0})\n'
                    '#$t=gcd_($t,{0});\n'
                    '#endif\n'
                    '#else\n'
                    '#$t={0};\n'
                    '#endif'
                ).format(p._id))
            elif p != 0:
                form.write((
                    '#if termsin($t)\n'
                    '#$t=gcd_($t,{0});\n'
                    '#else\n'
                    '#$t={0};\n'
                    '#endif'
                ).format(p))
        return Polynomial('$t', False)


def lcm(*polynomials):
    """Return the least common multiple of the given polynomials.

    Examples
    --------
    >>> p1 = Polynomial('(1+x)^1*(2+x)^3')
    >>> p2 = Polynomial('(1+x)^2*(2+x)^1')
    >>> lcm(p1, p2)
    Polynomial('8+28*x+38*x^2+25*x^3+8*x^4+x^5')

    """
    if (polynomials and len(polynomials) == 1 and
            isinstance(polynomials[0], (tuple, list, set, frozenset))):
        polynomials = polynomials[0]

    if any(not isinstance(p, (Polynomial, integer_types))
           for p in polynomials):
        raise TypeError('polynomial expected: {0}'.format(', '.join(
            repr(p) for p in polynomials
            if not isinstance(p, (Polynomial, integer_types))
        )))

    if not polynomials:
        raise TypeError('lcm() takes one or more arguments')
    if len(polynomials) == 1:
        # LCM(a) = a.
        if isinstance(polynomials, (set, frozenset)):
            polynomials = tuple(polynomials)
        return (polynomials[0] if isinstance(polynomials[0], Polynomial)
                else Polynomial(polynomials[0], False))

    form = Polynomial.get_instance()

    # LCM(a, b) = a b / GCD(a, b),
    # LCM(a, 0) = LCM(0, a) = LCM(0, 0) = 0.

    form.write('#$t=1;')
    for p in polynomials:
        if isinstance(p, Polynomial):
            form.write((
                '#if (termsin($t)!=0) && (termsin({0})!=0)\n'
                '#$t1=$t*{0};\n'
                '#$t2=gcd_($t,{0});\n'
                '#$t=div_($t1,$t2);\n'
                '#else\n'
                '#$t=0;\n'
                '#endif'
            ).format(p._id))
        elif p != 0:
            form.write((
                '#if termsin($t)\n'
                '#$t1=$t*{0};\n'
                '#$t2=gcd_($t,{0});\n'
                '#$t=div_($t1,$t2);\n'
                '#else\n'
                '#$t=0;\n'
                '#endif'
            ).format(p))
        else:
            return Polynomial(0, False)
    return Polynomial('$t', False)
