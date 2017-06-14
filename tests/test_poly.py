"""Test cases for form.poly."""

import unittest

from form.poly import Polynomial, gcd, lcm

form = Polynomial.get_instance()

# unittest in Python 2.6 doesn't have skipIf.
if not hasattr(unittest, 'skipIf'):
    unittest.skipIf = lambda condition, reason: (
        (lambda x: None) if condition else (lambda x: x))


class FormPolyTestCase(unittest.TestCase):
    """Test cases.

    Note that some of the tests require the fix by
    v4.1-20131025-109-gb32e53e [2015-08-05] for large polynomials.
    """

    def setUp(self):
        """Set up test fixture."""
        form.open(None, 5)

    def test_hook(self):
        """Test for hook installation."""
        def hook1(f):
            f.write('''
                #define h1 "11"
            ''')

        def hook2(f):
            f.write('''
                #define h2 "22"
            ''')

        form = Polynomial.get_instance()
        form.install_hook(hook1)
        form.install_hook(hook1)  # A duplicated should be ignored.

        # Reopen the connection.
        form.open()

        # Install hooks.
        form.install_hook('''
            #procedure TestProc(x)
              #redefine `x' "{``x''+1}"
            #endprocedure
        ''')
        form.install_hook(hook2)
        form.install_hook(hook2)  # A duplicated should be ignored.

        # "AutoDeclare S *" should work without any problem.
        p = Polynomial('1+x')**2
        p_ref = Polynomial('1+2*x+x^2')
        self.assertEqual(p, p_ref)

        # TestProc should be also available.
        form.write('''
            #define a "1"
            #call TestProc(a)
        ''')
        self.assertEqual(form.read("`a'"), '2')

        # Check for the two hook functons.
        self.assertEqual(form.read("`h1'"), '11')
        self.assertEqual(form.read("`h2'"), '22')

    def test_erroneous_input(self):
        """Test for erroneous polynomial input."""
        # These errors are raised at the Python layer. FORM doesn't terminate.
        self.assertRaises(TypeError, Polynomial, object())  # invalid type
        self.assertRaises(ValueError, Polynomial, '1+&x')  # invalid char
        self.assertRaises(ValueError, Polynomial, 'x+')  # incomplete
        self.assertRaises(ValueError, Polynomial, 'x*')  # incomplete
        self.assertRaises(ValueError, Polynomial, 'x^')  # incomplete
        self.assertRaises(ValueError, Polynomial, '(x')  # incomplete
        self.assertRaises(ValueError, Polynomial, '() x')  # invalid
        self.assertRaises(ValueError, Polynomial, '(1+x) (y)')  # two exprs
        self.assertRaises(ValueError, Polynomial, '1+x^y')  # exp_
        self.assertRaises(ValueError, Polynomial, 'x+1/(1+x)')  # denom_

    def test_hashable(self):
        """Test for the hashable nature of polynomials."""
        lst1 = [Polynomial(x) for x in ('a', 'b', 'c', 'f')]
        lst2 = [Polynomial(x) for x in ('a', 'c', 'd', 'e')]
        lst3 = [Polynomial(x) for x in ('a', 'b', 'c', 'd', 'e', 'f')]
        set1 = set(lst1) | set(lst2)
        set2 = set(lst3)
        self.assertEqual(set1, set2)

    def test_copy(self):
        """Test for copy/deepcopy."""
        import copy
        p1 = Polynomial('1+x')
        p2 = copy.copy(p1)
        p3 = copy.deepcopy(p2)
        self.assertEqual(p1, p2)
        self.assertEqual(p1, p3)
        self.assertEqual(id(p1), id(p2))
        self.assertNotEqual(id(p1), id(p3))
        self.assertEqual(p1._id, p2._id)
        self.assertNotEqual(p1._id, p3._id)

    @unittest.skipIf(form._dateversion < 20150805, 'form bug')
    def test_expand(self):
        """Test basic polynomial operations."""
        p = Polynomial('1+x+y+z')**15
        q = p + Polynomial('w')
        r = p * q
        self.assertEqual(len(r), 6272)

    def test_erroneous_operation(self):
        """Test for erroneous polynomial operations."""
        p = Polynomial('1+x')
        q = Polynomial('1-x')
        z = Polynomial(0)
        o = object()

        self.assertRaises(TypeError, lambda: p == o)
        self.assertRaises(TypeError, lambda: p != o)
        self.assertRaises(TypeError, lambda: p + o)
        self.assertRaises(TypeError, lambda: p - o)
        self.assertRaises(TypeError, lambda: p * o)
        self.assertRaises(TypeError, lambda: p ** o)
        self.assertRaises(TypeError, lambda: p // o)
        self.assertRaises(TypeError, lambda: p % o)
        self.assertRaises(TypeError, lambda: p / o)

        self.assertRaises(TypeError, lambda: o == p)
        self.assertRaises(TypeError, lambda: o != p)
        self.assertRaises(TypeError, lambda: o + p)
        self.assertRaises(TypeError, lambda: o - p)
        self.assertRaises(TypeError, lambda: o * p)
        self.assertRaises(TypeError, lambda: o ** p)
        self.assertRaises(TypeError, lambda: o // p)
        self.assertRaises(TypeError, lambda: o % p)
        self.assertRaises(TypeError, lambda: o / p)

        self.assertRaises(ZeroDivisionError, lambda: p // 0)
        self.assertRaises(ZeroDivisionError, lambda: p % 0)
        self.assertRaises(ZeroDivisionError, lambda: p / 0)
        self.assertRaises(ZeroDivisionError, lambda: p / z)
        self.assertRaises(ZeroDivisionError, lambda: 1 / z)
        self.assertRaises(TypeError, lambda: p / q)
        self.assertRaises(TypeError, lambda: 1 / p)

    def test_attr(self):
        """Test for polynomial attributes."""
        from fractions import Fraction
        p0 = Polynomial(0)
        p1 = Polynomial(1)
        p2 = Polynomial(-9)
        p3 = Polynomial(Fraction(3, 8))
        p4 = Polynomial('x')
        p5 = Polynomial('x*y')
        p6 = Polynomial('2*x*y')
        p7 = Polynomial('-1+x')

        pp = (p0, p1, p2, p3, p4, p5, p6, p7)

        self.assertEqual(
            [p.is_zero for p in pp],
            [True, False, False, False, False, False, False, False]
        )

        self.assertEqual(
            [p.is_one for p in pp],
            [False, True, False, False, False, False, False, False]
        )

        self.assertEqual(
            [p.is_integer for p in pp],
            [True, True, True, False, False, False, False, False]
        )

        self.assertEqual(
            [p.is_number for p in pp],
            [True, True, True, True, False, False, False, False]
        )

        self.assertEqual(
            [p.is_symbol for p in pp],
            [False, False, False, False, True, False, False, False]
        )

        self.assertEqual(p1.integer, 1)
        self.assertEqual(p1.fraction, 1)

        self.assertRaises(ValueError, lambda: p3.integer)
        self.assertEqual(p3.fraction, Fraction(3, 8))

        self.assertRaises(ValueError, lambda: p4.integer)
        self.assertRaises(ValueError, lambda: p4.fraction)

        self.assertEqual(p0.unit, 0)
        self.assertEqual(p1.unit, 1)
        self.assertEqual(p2.unit, -1)
        self.assertEqual(p3.unit, 1)
        self.assertEqual(p4.unit, 1)
        self.assertEqual(p5.unit, 1)
        self.assertEqual(p6.unit, 1)
        self.assertEqual(p7.unit, -1)

    def test_factorize(self):
        """Test polynomial factorization."""
        p1 = Polynomial('-3+x*y')
        p2 = Polynomial('y')
        p3 = Polynomial('y')
        p4 = Polynomial('-x^2+2*y')
        p5 = Polynomial(-2)
        p = p1 * p2 * p3 * p4 * p5
        fac = tuple(p.factorize())
        if form._dateversion >= 20150831:
            self.assertEqual(fac, (p1, p2, p3, p4, p5))
        else:
            self.assertEqual(fac, (p1, p5, p2, p3, p4))

    def test_degree(self):
        """Test for Polynomial.degree()."""
        p = Polynomial('1+x')
        q = Polynomial('1-x')
        o = object()

        self.assertRaises(ValueError, lambda: p.degree('1+x'))
        self.assertRaises(ValueError, lambda: p.degree('x*y'))
        self.assertRaises(ValueError, lambda: p.degree(q))
        self.assertRaises(TypeError, lambda: p.degree(o))
        self.assertRaises(ValueError, lambda: p.degree('x', lambda x: x))

        self.assertEqual(p.degree('y', max), 0)
        self.assertEqual(p.degree('y', min), 0)
        self.assertEqual(p.degree('y', list), [0, 0])
        self.assertEqual(p.degree('y', set), set([0, 0]))

        p = Polynomial(0)

        self.assertEqual(p.degree('x', max), 0)
        self.assertEqual(p.degree('x', min), 0)
        self.assertEqual(p.degree('x', list), [])
        self.assertEqual(p.degree('x', set), set([]))

        p = Polynomial('x^3 + x^8 + x^10') * Polynomial('1+y')
        x = Polynomial('x')

        self.assertEqual(p.degree(x), 10)
        self.assertEqual(p.degree(x, min), 3)
        self.assertEqual(p.degree(x, list), [3, 3, 8, 8, 10, 10])
        self.assertEqual(p.degree(x, set), set([3, 8, 10]))

        self.assertEqual(p.degree(x, max, False), 10)

    def test_coefficient(self):
        """Test for Polynomial.coefficient()."""
        p = Polynomial('1+x')
        q = Polynomial('1-x')
        x = Polynomial('x')
        o = object()

        self.assertRaises(ValueError, lambda: p.coefficient('1+x', 1))
        self.assertRaises(ValueError, lambda: p.coefficient('x*y', 1))
        self.assertRaises(ValueError, lambda: p.coefficient(q, 1))
        self.assertRaises(TypeError, lambda: p.coefficient(o, 1))
        self.assertRaises(TypeError, lambda: p.coefficient('x', '1'))

        p = Polynomial('2+x+3*x*y+x^2')

        self.assertEqual(p.coefficient('x', 0), 2)
        self.assertEqual(p.coefficient('x', 1), Polynomial('1+3*y'))
        self.assertEqual(p.coefficient('y', 1), Polynomial('3*x'))
        self.assertEqual(p.coefficient('z', 1), 0)
        self.assertEqual(p.coefficient(x, 2), 1)

        self.assertEqual(p.coefficient(x, 2, False), 1)

    def test_diff(self):
        """Test for Polynomial.diff()."""
        p = Polynomial('1+x')
        q = Polynomial('1-x')
        o = object()

        self.assertRaises(ValueError, lambda: p.diff('1+x'))
        self.assertRaises(ValueError, lambda: p.diff('x*y'))
        self.assertRaises(ValueError, lambda: p.diff(q))
        self.assertRaises(TypeError, lambda: p.diff(o))
        self.assertRaises(TypeError, lambda: p.diff('x', o))
        self.assertRaises(TypeError, lambda: p.diff('x', -1))

        p = Polynomial('2+x+3*x*y+x^2')
        x = Polynomial('x')

        self.assertEqual(p.diff('x', 0), p)
        self.assertEqual(p.diff('x'), Polynomial('1+3*y+2*x'))
        self.assertEqual(p.diff('x', 1), Polynomial('1+3*y+2*x'))
        self.assertEqual(p.diff('x', 2), 2)
        self.assertEqual(p.diff('x', 3), 0)
        self.assertEqual(p.diff('x', 4), 0)

        self.assertEqual(p.diff(x), Polynomial('1+3*y+2*x'))
        self.assertEqual(p.diff(x, 1, False), Polynomial('1+3*y+2*x'))

    def test_subs(self):
        """Test for Polynomial.subs()."""
        p = Polynomial('1+x')
        q = Polynomial('1-x')
        o = object()

        self.assertRaises(ValueError, lambda: p.subs('1+x', q))
        self.assertRaises(ValueError, lambda: p.subs('2*x*y', q))
        self.assertRaises(ValueError, lambda: p.subs(p, q))
        self.assertRaises(TypeError, lambda: p.subs(o, q))
        self.assertRaises(TypeError, lambda: p.subs('x', o))

        p = Polynomial('(1+x+y+z)*(1-x)')
        x = Polynomial('x')
        u = Polynomial(1)

        self.assertEqual(p.subs('w', '1'), p)
        self.assertEqual(p.subs('x', '1'), 0)
        self.assertEqual(p.subs('x', u), 0)
        self.assertEqual(p.subs(x, '1'), 0)
        self.assertEqual(p.subs(x, u), 0)

        p = Polynomial('(1+x+y)^4')
        self.assertEqual(
            p.subs('x*y^2', '-1'),
            Polynomial(('-11+6*y^2+4*y^3+y^4-2*x+12*x*y+6*x^2+12*x^2*y+4*x^3'
                        '+4*x^3*y+x^4'))
        )

    def test_gcd(self):
        """Test polynomial GCD (1)."""
        o = object()

        self.assertRaises(TypeError, lambda: gcd())
        self.assertRaises(TypeError, lambda: gcd([1, o, 3]))

        self.assertEqual(gcd([0, 0]), 0)
        self.assertEqual(gcd([0, 3]), 3)
        self.assertEqual(gcd([7, 0]), 7)
        self.assertEqual(gcd([-6]), -6)

        p0 = Polynomial(0)
        p1 = Polynomial('(1+x)^3')
        p2 = Polynomial('1-x^2')
        p3 = Polynomial('1+x')

        self.assertEqual(gcd(p0), p0)
        self.assertEqual(gcd(p1), p1)
        self.assertEqual(gcd(p0, p1), p1)
        self.assertEqual(gcd(p1, p2), p3)
        self.assertEqual(gcd(p0, p1, p0, p0, p2, p0), p3)

        self.assertEqual(gcd(set([p1])), p1)
        self.assertEqual(gcd(set([p1, p2])), p3)

    @unittest.skipIf(form._dateversion < 20150805, 'form bug')
    def test_gcd2(self):
        """Test polynomial GCD (2)."""
        e1 = Polynomial('(x^2+y+z+1)^3+(x-y*z+1)^2') + 4
        e2 = 1 - Polynomial('(x+y^2+z-1)^3+(x+y)^2')
        e3 = e2 + 10
        e4 = e1 + 1
        p1 = e1 ** 3 * e2 ** 3 * e4
        p2 = e1 ** 2 * e3 ** 4 * e4
        res = gcd(p1, p2)
        ref_res = e1 ** 2 * e4
        self.assertEqual(res, ref_res)

    def test_lcm1(self):
        """Test polynomial LCM (1)."""
        o = object()

        self.assertRaises(TypeError, lambda: lcm())
        self.assertRaises(TypeError, lambda: lcm([1, o, 3]))

        self.assertEqual(lcm([0, 0]), 0)
        self.assertEqual(lcm([0, 3]), 0)
        self.assertEqual(lcm([7, 0]), 0)
        self.assertEqual(lcm([-6]), -6)

        p0 = Polynomial(0)
        p1 = Polynomial('(1+x)^3')
        p2 = Polynomial('1-x^2')
        p3 = Polynomial('(1-x)*(1+x)^3')

        self.assertEqual(lcm(p0), 0)
        self.assertEqual(lcm(p1), p1)
        self.assertEqual(lcm(p0, p1), 0)
        self.assertEqual(lcm(p1, p2), p3)
        self.assertEqual(lcm(p0, p1, p0, p0, p2, p0), 0)

        self.assertEqual(lcm(set([p1])), p1)
        self.assertEqual(lcm(set([p1, p2])), p3)

    @unittest.skipIf(form._dateversion < 20150805, 'form bug')
    def test_lcm2(self):
        """Test polynomial LCM (2)."""
        e1 = Polynomial('1+x+y-z')
        e2 = Polynomial('2+x-y+z')
        e3 = Polynomial('-5+3*x*z')
        e4 = Polynomial('1-7*y+z^3')
        p1 = 10 * e1 ** 2 * e2
        p2 = - 7 * e1 ** 3 * e3 * e4
        p3 = 15 * e1 ** 4 * e2 * e4 ** 2
        res = lcm(p1, p2, p3)
        ref_res = 210 * e1 ** 4 * e2 * e3 * e4 ** 2
        self.assertEqual(res, ref_res)


if __name__ == '__main__':
    unittest.main()
