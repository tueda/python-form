"""Routines for polynomials via FORM."""

from . import singleton
from .parser import is_expression, is_lhs, is_symbol
from ..six import integer_types, string_types


class Polynomial(object):
    """Polynomial.

    An immutable polynomial object stored in the expanded form as a $-variable
    in FORM. Many standard operators are supported.

    Examples
    --------
    Create polynomials. All identifiers (matching to the regular expression
    ``[a-zA-Z][0-9a-zA-Z]*``) are recoginized as symbols:

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
    >>> len(p)
    5

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

    """

    _form = None  # The singleton.

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
            self._len = -1
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
        elif isinstance(expr, integer_types):
            self._id = self._form.next_id()
            self._str = None
            self._len = -1
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
        self._len = -1
        self._form.write('#{0}={1};'.format(self._id, state['s']))
        # self._form.check()

    def __str__(self):
        """Informal string representation."""
        if not self._str:
            self._str = self._form.read(self._id)
        return self._str

    def __repr__(self):
        """Formal string representation."""
        return "Polynomial('{0}')".format(str(self))

    def __hash__(self):
        """Hash value."""
        return hash(str(self))

    def __len__(self):
        """Return the number of terms."""
        if self._len == -1:
            self._form.write('#$t=termsin_({0});'.format(self._id))
            self._len = int(self._form.read('$t'))
        return self._len

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
            self._form.write('#$t={0}-{1};#$t=nterms_($t);'.format(
                self._id, other._id))
            return self._form.read('$t') == '0'
        if isinstance(other, integer_types):
            if other == 0:
                return len(self) == 0
            if len(self) != 1:
                return False
            self._form.write('#$t={0}-{1};#$t=nterms_($t);'.format(
                self._id, other))
            return self._form.read('$t') == '0'
        raise TypeError('polynomial expected: {0}'.format(repr(other)))

    def __ne__(self, other):
        """Return self != other."""
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
            return Polynomial('{0}*{1}'.format(self._id, other._id), False)
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
        >>> p = Polynomial('1+x')
        >>> q = Polynomial('1-x')
        >>> p / q
        RationalFunction('1+x', '1-x')

        """
        from .rat import RationalFunction
        if isinstance(other, (Polynomial, integer_types)):
            return RationalFunction(self, other)
        return NotImplemented

    def __rtruediv__(self, other):
        """Return other / self.

        Examples
        --------
        >>> p = Polynomial('1+x')
        >>> 1 / p
        RationalFunction('1', '1+x')

        """
        from .rat import RationalFunction
        if isinstance(other, integer_types):
            return RationalFunction(other, self)
        return NotImplemented

    # For Python 2.
    __div__ = __truediv__
    __rdiv__ = __rtruediv__

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

    def degree(self, x, f=max, check=True):
        """Return the degree with respect to ``x``.

        Return the degree with respect to ``x``, which must be a symbol.
        The second argument specifies how the set of exponents are treated:

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
        >>> p.degree('x', min)
        1
        >>> p.degree('x', list) == [1, 1, 3, 6]
        True
        >>> p.degree('x', set) == set([1, 3, 6])
        True

        """
        if isinstance(x, string_types):
            if check and not is_symbol(x):
                raise ValueError('symbol expected: {0}'.format(repr(x)))
        elif isinstance(x, Polynomial):
            if check and not is_symbol(str(x)):
                raise ValueError('symbol expected: {0}'.format(repr(x)))
            x = x._id
        else:
            raise TypeError('symbol expected: {0}'.format(repr(x)))

        if f is max:
            # XXX: the minimum power assumed.
            self._form.write((
                '#$t=-32768;\n'
                '#inside {0}\n'
                'if(count({1},1)>$t)$t=count_({1},1);'
                '#endinside'
            ).format(self._id, x))
            n = int(self._form.read('$t'))
            if n == -32768:
                n = 0
            return n
        if f is min:
            # XXX: the maximum power assumed.
            self._form.write((
                '#$t=32767;\n'
                '#inside {0}\n'
                'if(count({1},1)<$t)$t=count_({1},1);'
                '#endinside'
            ).format(self._id, x))
            n = int(self._form.read('$t'))
            if n == 32767:
                n = 0
            return n
        if f is list:
            # XXX: intended for small polynomials.
            self._form.write((
                '#$t=dum_();\n'
                '#inside {0}\n'
                '$t1=count_({1},1);'
                'inside $t;'
                'id dum_(?a)=dum_(?a,$t1);'
                'endinside;'
                '#endinside'
            ).format(self._id, x))
            s = self._form.read('$t')[1:-1]
            if not s:
                return []
            return [int(i) for i in s.split(',')]
        if f is set:
            return set(self.degree(x, list))
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
            if check and not is_symbol(str(x)):
                raise ValueError('symbol expected: {0}'.format(repr(x)))
            x = str(x)
        else:
            raise TypeError('symbol expected: {0}'.format(repr(x)))

        if not isinstance(n, integer_types):
            raise TypeError('integer expected: {0}'.format(repr(n)))

        r = Polynomial(self, False)
        self._form.write((
            '#inside {0}\n'
            'if(count({1},1)!={2})discard;'
            'multiply 1/{1}^{2};\n'
            '#endinside'
        ).format(r._id, x, n))
        return r

    def subs(self, lhs, rhs, check=True):
        """Return the result of an algebraic replacement.

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
            if check and not is_lhs(str(lhs)):
                raise ValueError('lhs expected: {0}'.format(repr(lhs)))
            p1 = lhs
            lhs = p1._id  # XXX: assume valid until the end
        else:
            raise TypeError('lhs expected: {0}'.format(repr(lhs)))

        if isinstance(rhs, string_types):
            if check:
                p2 = Polynomial(rhs, True)
                rhs = p2._id  # XXX: assume valid until the end
        elif isinstance(rhs, Polynomial):
            pass
        else:
            raise TypeError('rhs expected: {0}'.format(repr(rhs)))

        p = Polynomial(self, False)
        self._form.write((
            '#inside {0}\n'
            'id {1}={2};\n'
            '#endinside'
        ).format(p._id, lhs, rhs))
        return p


def gcd(*polynomials):
    """Return the greatest common divisor of the given polynomials.

    Examples
    --------
    >>> p1 = Polynomial('(1+x)^1*(2+x)^3')
    >>> p2 = Polynomial('(1+x)^2*(2+x)^1')
    >>> gcd(p1, p2)
    Polynomial('2+3*x+x^2')

    Note
    ----
    - The result may have an ambiguity in the unit, i.e., an extra ``-1``. This
      is not fixed for the sake of speed.
    - In the current implementation, ``gcd(0,0)`` returns 1, which is different
      from ``fractions.gcd`` and ``math.gcd``.

    """
    if (polynomials and len(polynomials) == 1 and
            isinstance(polynomials[0], (tuple, list))):
        polynomials = polynomials[0]
    if not polynomials:
        return Polynomial(1, False)
    if any(not isinstance(p, (Polynomial, integer_types))
           for p in polynomials):
        raise TypeError('polynomial expected: {0}'.format(', '.join(
            repr(p) for p in polynomials
            if not isinstance(p, (Polynomial, integer_types))
        )))
    return Polynomial('gcd_({0})'.format(','.join((
        p._id if isinstance(p, Polynomial) else str(p)
    ) for p in polynomials)), False)


def lcm(*polynomials):
    """Return the least common multiple of the given polynomials.

    Examples
    --------
    >>> p1 = Polynomial('(1+x)^1*(2+x)^3')
    >>> p2 = Polynomial('(1+x)^2*(2+x)^1')
    >>> lcm(p1, p2)
    Polynomial('8+28*x+38*x^2+25*x^3+8*x^4+x^5')

    Note
    ----
    The result may have an ambiguity in the unit, i.e., an extra ``-1``. This
    is not fixed for the sake of speed.

    """
    if (polynomials and len(polynomials) == 1 and
            isinstance(polynomials[0], (tuple, list))):
        polynomials = polynomials[0]
    if not polynomials:
        raise TypeError('polynomials expected: {0}'.format(repr(polynomials)))
    if any(not isinstance(p, (Polynomial, integer_types))
           for p in polynomials):
        raise TypeError('polynomial expected: {0}'.format(', '.join(
            repr(p) for p in polynomials
            if not isinstance(p, (Polynomial, integer_types))
        )))
    form = Polynomial.get_instance()
    form.write('#$t=1;')
    for p in polynomials:
        form.write((
            '#$t1=$t*{0};'
            '#$t2=gcd_($t,{0});'
            '#$t=div_($t1,$t2);'
        ).format(p._id if isinstance(p, Polynomial) else p))
    return Polynomial('$t', False)
