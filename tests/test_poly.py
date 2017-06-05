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

    def test_factor(self):
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

    @unittest.skipIf(form._dateversion < 20150805, 'form bug')
    def test_gcd(self):
        """Test polynomial GCD."""
        e1 = Polynomial('(x^2+y+z+1)^3+(x-y*z+1)^2') + 4
        e2 = 1 - Polynomial('(x+y^2+z-1)^3+(x+y)^2')
        e3 = e2 + 10
        e4 = e1 + 1
        p1 = e1 ** 3 * e2 ** 3 * e4
        p2 = e1 ** 2 * e3 ** 4 * e4
        res = gcd(p1, p2)
        ref_res = e1 ** 2 * e4
        self.assertEqual(res, ref_res)

    @unittest.skipIf(form._dateversion < 20150805, 'form bug')
    def test_lcm(self):
        """Test polynomial LCM."""
        e1 = Polynomial('1+x+y-z')
        e2 = Polynomial('2+x-y+z')
        e3 = Polynomial('5+3*x*z')
        e4 = Polynomial('1-7*y+z^3')
        p1 = 10 * e1 ** 2 * e2
        p2 = - 7 * e1 ** 3 * e3 * e4
        p3 = 15 * e1 ** 4 * e2 * e4 ** 2
        res = lcm(p1, p2, p3)
        ref_res = 210 * e1 ** 4 * e2 * e3 * e4 ** 2
        self.assertEqual(res, ref_res)


if __name__ == '__main__':
    unittest.main()
