import unittest
import form

class FormTestCase(unittest.TestCase):
    def test_FormLink(self):
        with form.open() as fl:
            fl.write('''
                AutoDeclare Vector p;
                Local F = g_(0,p1,...,p6);
                trace4,0;
                .sort
            ''')
            str_F = fl.read('F')
            fl.write('''
                #$n = termsin_(F);
            ''')
            str_n = fl.read('$n')
            str_z = fl.read("`ZERO_F'")
            self.assertEqual(str_F, '\
4*p1.p2*p3.p4*p5.p6-4*p1.p2*p3.p5*p4.p6+4*p1.p2*p3.p6*p4.p5\
-4*p1.p3*p2.p4*p5.p6+4*p1.p3*p2.p5*p4.p6-4*p1.p3*p2.p6*p4.p5\
+4*p1.p4*p2.p3*p5.p6-4*p1.p4*p2.p5*p3.p6+4*p1.p4*p2.p6*p3.p5\
-4*p1.p5*p2.p3*p4.p6+4*p1.p5*p2.p4*p3.p6-4*p1.p5*p2.p6*p3.p4\
+4*p1.p6*p2.p3*p4.p5-4*p1.p6*p2.p4*p3.p5+4*p1.p6*p2.p5*p3.p4\
')
            self.assertEqual(str_n, '15')
            self.assertEqual(str_z, '0')

if __name__ == '__main__':
    unittest.main()
