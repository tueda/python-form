import unittest
import form

class FormTestCase(unittest.TestCase):
    def test_basic(self):
        with form.open() as f:
            f.write('''
                AutoDeclare Vector p;
                Local F = g_(0,p1,...,p6);
                trace4,0;
                .sort
            ''')
            str_F = f.read('F')
            f.write('''
                #$n = termsin_(F);
            ''')
            str_n = f.read('$n')
            str_z = f.read("`ZERO_F'")

        self.assertEqual(str_F, '\
4*p1.p2*p3.p4*p5.p6-4*p1.p2*p3.p5*p4.p6+4*p1.p2*p3.p6*p4.p5\
-4*p1.p3*p2.p4*p5.p6+4*p1.p3*p2.p5*p4.p6-4*p1.p3*p2.p6*p4.p5\
+4*p1.p4*p2.p3*p5.p6-4*p1.p4*p2.p5*p3.p6+4*p1.p4*p2.p6*p3.p5\
-4*p1.p5*p2.p3*p4.p6+4*p1.p5*p2.p4*p3.p6-4*p1.p5*p2.p6*p3.p4\
+4*p1.p6*p2.p3*p4.p5-4*p1.p6*p2.p4*p3.p5+4*p1.p6*p2.p5*p3.p4\
')
        self.assertEqual(str_n, '15')
        self.assertEqual(str_z, '0')

    def test_multiple_read(self):
        with form.open() as f:
            f.write('''
                S x;
                L F1 = (1+x)^2;
                L F2 = (1-x)^2;
                .sort
            ''')
            str_FF = f.read('F1', 'F2')

        self.assertEqual(str_FF, ('1+2*x+x^2', '1-2*x+x^2'))

    def test_old_style(self):
        f = form.open()
        try:
            f.write('''
                S x;
                L F = (1+x)^2;
                .sort
            ''')
            self.assertEqual(f.read('F'), '1+2*x+x^2')
            self.assertEqual(f.closed, False)
        finally:
            f.close()
        self.assertEqual(f.closed, True)

    def test_arguments(self):
        with form.open('form -D N1=123 -D N2=456') as f:
            self.assertEqual(f.read("`N1'"), '123')
            self.assertEqual(f.read("`N2'"), '456')

        with form.open(('form', '-D', 'N1=123', '-D', 'N2=456')) as f:
            self.assertEqual(f.read("`N1'"), '123')
            self.assertEqual(f.read("`N2'"), '456')

    def test_flush(self):
        with form.open() as f:
            N = 9
            M = 10
            f.write('''
                #define N "{0}"
                #define M "{1}"
                S x1,...,x`N';
                L F = (x1+...+x`N')^`M';
                .sort
                #do i=1,`N'
                  id x`i' = 1;
                #enddo
                .sort
            '''.format(N, M))
            # The following calls of flush() must be irrelevant.
            f.flush()
            f.flush()
            f.flush()
            f.flush()
            self.assertEqual(f.read("F"), str(N**M))

if __name__ == '__main__':
    unittest.main()
