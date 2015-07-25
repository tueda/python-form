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

if __name__ == '__main__':
    unittest.main()
