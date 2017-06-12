"""Test cases for form.poly with multiprocessing."""

import unittest

from form.poly import Polynomial

# unittest in Python 2.6 doesn't have skipIf.
if not hasattr(unittest, 'skipIf'):
    unittest.skipIf = lambda condition, reason: (
        (lambda x: None) if condition else (lambda x: x))


def get_mp_context():
    """Return a compatible context for multiprocessing."""
    try:
        # The easiest way not to share the pipes is to use ``forkserver``.
        # It works with CPython 3.4 or later on UNIX.
        import multiprocessing
        mp = multiprocessing.get_context('forkserver')
        return mp
    except (AttributeError, ValueError):
        pass
    return None


def func_pool(arg):
    """Test worker function."""
    p = arg[0]
    n = arg[1]
    return p**n


class FormPolyMpTestCase(unittest.TestCase):
    """Test cases."""

    @unittest.skipIf(get_mp_context() is None, 'forkserver unavailable')
    def test_pool(self):
        """Test on multiprocessing.Pool."""
        mp = get_mp_context()
        p = Polynomial('1+x+y')
        pool = mp.Pool(4)
        res = list(pool.map(func_pool, [(p, n) for n in range(10)]))
        ref_res = list(map(func_pool, [(p, n) for n in range(10)]))
        self.assertEqual(res, ref_res)


if __name__ == '__main__':
    unittest.main()
