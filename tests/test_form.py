"""Test cases for form."""

import unittest

import form
from form import FormError


class FormTestCase(unittest.TestCase):
    """Test cases."""

    def test_basic(self):
        """Basic tests for FormLink."""
        import re

        with form.open() as f:
            f.write(
                """
                AutoDeclare Vector p;
                Local F = g_(0,p1,...,p6);
                trace4,0;
                .sort
            """
            )
            str_f = f.read("F")
            f.write(
                """
                #$n = termsin_(F);
            """
            )
            str_n = f.read("$n")
            str_z = f.read("`ZERO_F'")

        self.assertEqual(
            str_f,
            re.sub(
                r"\s+",
                "",
                """
            4*p1.p2*p3.p4*p5.p6-4*p1.p2*p3.p5*p4.p6+4*p1.p2*p3.p6*p4.p5
            -4*p1.p3*p2.p4*p5.p6+4*p1.p3*p2.p5*p4.p6-4*p1.p3*p2.p6*p4.p5
            +4*p1.p4*p2.p3*p5.p6-4*p1.p4*p2.p5*p3.p6+4*p1.p4*p2.p6*p3.p5
            -4*p1.p5*p2.p3*p4.p6+4*p1.p5*p2.p4*p3.p6-4*p1.p5*p2.p6*p3.p4
            +4*p1.p6*p2.p3*p4.p5-4*p1.p6*p2.p4*p3.p5+4*p1.p6*p2.p5*p3.p4
        """,
            ),
        )
        self.assertEqual(str_n, "15")
        self.assertEqual(str_z, "0")

    def test_multiple_read(self):
        """Test multiple arguments for FormLink.read()."""
        with form.open() as f:
            f.write(
                """
                S x;
                L F1 = (1+x)^2;
                L F2 = (1-x)^2;
                .sort
            """
            )
            self.assertEqual(f.read(), None)
            self.assertEqual(f.read("F1", "F2"), ["1+2*x+x^2", "1-2*x+x^2"])

    def test_old_style(self):
        """Tests without the "with" statement."""
        f = form.open()
        try:
            f.write(
                """
                S x;
                L F = (1+x)^2;
                .sort
            """
            )
            self.assertEqual(f.read("F"), "1+2*x+x^2")
            self.assertEqual(f.closed, False)
        finally:
            f.close()
        self.assertEqual(f.closed, True)

    def test_arguments(self):
        """Test complicated arguments for FormLink.open()."""
        with form.open("form -D N1=123 -D N2=456") as f:
            self.assertEqual(f.read("`N1'"), "123")
            self.assertEqual(f.read("`N2'"), "456")

        with form.open(("form", "-D", "N1=123", "-D", "N2=456")) as f:
            self.assertEqual(f.read("`N1'"), "123")
            self.assertEqual(f.read("`N2'"), "456")

    def test_flush(self):
        """Tests for FormLink.flush()."""
        with form.open() as f:
            n = 9
            m = 10
            f.write(
                """
                #define N "{0}"
                #define M "{1}"
                S x1,...,x`N';
                L F = (x1+...+x`N')^`M';
                .sort
                #do i=1,`N'
                    id x`i' = 1;
                #enddo
                .sort
            """.format(
                    n, m
                )
            )
            # The following calls of flush() must be irrelevant.
            f.flush()
            f.flush()
            f.flush()
            f.flush()
            self.assertEqual(f.read("F"), str(n ** m))

    def test_errors(self):
        """Tests for erroneous cases."""
        # Undeclared symbols.
        with form.open() as f:
            f.write(
                """
                L F = (1+x)^2;
                .sort
            """
            )
            self.assertRaises(FormError, f.read, "F")

        # Undefined expressions.
        with form.open() as f:
            f.write(
                """
                S x;
                L F = (1+x)^2;
                .sort
            """
            )
            self.assertRaises(FormError, f.read, "G")

        # Accesses to closed connections.
        with form.open() as f:
            f.close()
            self.assertRaises(IOError, f.write, "")
            self.assertRaises(IOError, f.flush)
            self.assertRaises(IOError, f.read)

    def test_many_times(self):
        """Test with many reads/writes."""
        with form.open() as f:
            n = 2000
            f.write(
                """
                #$x = 0;
            """
            )
            for _ in range(n):
                f.write(
                    """
                    #$x = $x + 1;
                """
                )
                f.read("$x")
            self.assertEqual(int(f.read("$x")), n)

    def test_keep_log(self):
        """Tests with keep_log."""
        script = """
            On stats;
            S x;
            L F = (1+x)^2;
            ;* 1
            ;* 2
            ;* 3
            ;* 4
            ;* 5
            ;* 6
            ;* 7
            ;* 8
            ;* 9
            ;* 10
            L G = (1-x)^2;
            ;* 1
            ;* 2
            ;* 3
            ;* 4
            ;* 5
            ;* 6
            ;* 7
            ;* 8
            ;* 9
            ;* 10
            .sort
        """

        with form.open() as f:
            msg = None
            f.write(script)
            try:
                f.read("X")
            except FormError as e:
                msg = str(e)
            self.assertTrue(msg is not None)
            # Neither F nor G appears in `msg`.
            self.assertTrue(msg.find("L F = (1+x)^2;") < 0)
            self.assertTrue(msg.find("L G = (1-x)^2;") < 0)

        with form.open(keep_log=True) as f:
            msg = None
            f.write(script)
            try:
                f.read("X")
            except FormError as e:
                msg = str(e)
            self.assertTrue(msg is not None)
            # Both F and G appear in `msg`.
            self.assertTrue(msg.find("L F = (1+x)^2;") >= 0)
            self.assertTrue(msg.find("L G = (1-x)^2;") >= 0)

        with form.open(keep_log=30) as f:
            msg = None
            f.write(script)
            try:
                f.read("X")
            except FormError as e:
                msg = str(e)
            self.assertTrue(msg is not None)
            # G is still in `msg' but F is not.
            self.assertTrue(msg.find("L F = (1+x)^2;") < 0)
            self.assertTrue(msg.find("L G = (1-x)^2;") >= 0)

    def test_seq_args(self):
        """Test complicated arguments for FormLink.read()."""
        with form.open() as f:
            f.write(
                """
                #do i=1,9
                    L F`i' = `i';
                #enddo
                .sort
            """
            )
            # normal arguments
            self.assertEqual(f.read("F1"), "1")
            self.assertEqual(f.read("F1", "F2"), ["1", "2"])
            self.assertEqual(f.read("F1", "F2", "F3"), ["1", "2", "3"])
            # a non-string argument
            self.assertEqual(f.read(("F1",)), ["1"])
            self.assertEqual(f.read(("F1", "F2")), ["1", "2"])
            self.assertEqual(f.read(("F1", "F2", "F3")), ["1", "2", "3"])
            # a generator
            self.assertEqual(f.read("F{0}".format(i) for i in range(1, 2)), ["1"])
            self.assertEqual(f.read("F{0}".format(i) for i in range(1, 3)), ["1", "2"])
            self.assertEqual(
                f.read("F{0}".format(i) for i in range(1, 4)), ["1", "2", "3"]
            )
            # more complicated arguments
            self.assertEqual(f.read(["F1"], "F2"), [["1"], "2"])
            self.assertEqual(f.read(["F1"], ["F2"]), [["1"], ["2"]])
            self.assertEqual(f.read("F1", ["F2", "F3"]), ["1", ["2", "3"]])
            self.assertEqual(f.read("F1", ["F2"], ["F3"]), ["1", ["2"], ["3"]])
            self.assertEqual(
                f.read(["F1"], ["F2", ["F3", "F4"]]), [["1"], ["2", ["3", "4"]]]
            )
            self.assertEqual(
                f.read("F1", (("F{0}").format(i) for i in range(2, 5))),
                ["1", ["2", "3", "4"]],
            )

    def test_long_lines(self):
        """Test with long lines."""
        with form.open() as f:
            f.write(
                """
                L F = 2^1000;
                #$x = 2^1000;
                .sort
                #define x "`$x'"
            """
            )
            answer = str(2 ** 1000)
            self.assertEqual(f.read("F"), answer)
            self.assertEqual(f.read("$x"), answer)
            self.assertEqual(f.read("`x'"), answer)

    def test_empty_lines(self):
        """Test input with empty lines."""
        with form.open() as f:
            f.write(
                """
                On stats;

                S x;

                L F = (1+x)^2;


                .sort
            """
            )
            self.assertEqual(f.read("F"), "1+2*x+x^2")

    def test_factdollar(self):
        """Tests with factorized $-variables."""

        def join(factors):
            return "({0})".format(")*(".join(factors))

        def check_factors(x, factors):
            self.assertEqual(f.read("{0}[0]".format(x)), str(len(factors)))
            for i in range(len(factors)):
                self.assertEqual(f.read("{0}[{1}]".format(x, i + 1)), factors[i])
            self.assertEqual(f.read("{0}[]".format(x)), join(factors))

        with form.open() as f:
            # NOTE: The order of factors was changed by the version
            #       v4.1-20131025-112-g8805b9e [2015-08-31].
            f.write(
                """
                S a,b;
                #$x = (-5)*(a^5-b^5);
                #factdollar $x
            """
            )
            if f._dateversion >= 20150831:
                factors = ("b-a", "b^4+a*b^3+a^2*b^2+a^3*b+a^4", "5")
            else:
                factors = ("5", "b-a", "b^4+a*b^3+a^2*b^2+a^3*b+a^4")
            self.assertEqual(f.read("$x"), "5*b^5-5*a^5")
            check_factors("$x", factors)

            f.write(
                """
                S a,b;
                #$x = (a+b)^3;
                #factdollar $x
            """
            )
            factors = ("b+a", "b+a", "b+a")
            check_factors("$x", factors)

            f.write(
                """
                #$y = 0;
            """
            )
            self.assertEqual(f.read("$y[]"), "(0)")
            f.write(
                """
                #factdollar $y
            """
            )
            self.assertEqual(f.read("$y[]"), "(0)")

            f.write(
                """
                #$z = a;
            """
            )
            self.assertEqual(f.read("$z[]"), "a")
            f.write(
                """
                #factdollar $z
            """
            )
            self.assertEqual(f.read("$z[]"), "(a)")

            f.write(
                """
                #$w = 2*a;
            """
            )
            self.assertEqual(f.read("$w[]"), "2*a")
            f.write(
                """
                #factdollar $w
            """
            )
            if f._dateversion >= 20150903:
                factors = ("a", "2")
            else:
                factors = ("2", "a")
            check_factors("$w", factors)

    def test_kill(self):
        """Tests for FormLink.kill()."""
        import signal
        import time

        with form.open() as f:

            def cb_timeout_handler(signum, frame):
                raise RuntimeError("Timeout")

            def do_test(func):
                f.write(
                    """
                    Auto V p;
                    L F = g_(0,p1,...,p30);
                    trace4,0;
                    .sort
                """
                )
                f.flush()
                time.sleep(0.5)

                signal.signal(signal.SIGALRM, cb_timeout_handler)
                signal.alarm(10)
                try:
                    func()
                finally:
                    signal.alarm(0)

            do_test(lambda: f.kill())
            f.open()
            do_test(lambda: f._close(term=True))
            f.open()
            do_test(lambda: f._close(term=True, kill=True))

    def test_head(self):
        """Test for FormLink.head."""
        with form.open() as f:
            head = f.head
            self.assertTrue(
                head[:4] == "FORM" or head[:5] == "TFORM" or head[:7] == "ParFORM"
            )

    def test_environ(self):
        """Test for $FORM."""
        import os

        old_form = os.environ.get("FORM", None)
        try:
            os.environ["FORM"] = "form -D X=12345"

            with form.open() as f:
                self.assertEqual(f.read("`X'"), "12345")
        finally:
            if old_form is None:
                del os.environ["FORM"]
            else:
                os.environ["FORM"] = old_form


if __name__ == "__main__":
    unittest.main()
