"""Routines for rational functions via FORM."""

from .parser import is_signed_integer, is_unsigned_integer
from .poly import Polynomial
from ..six import integer_types


class RationalFunction(object):
    """Rational function."""

    _form = None  # The singleton.

    @classmethod
    def get_instance(cls):
        """Return the FORM instance for polynomial arithmetic."""
        if cls._form is None:
            cls._form = Polynomial.get_instance()
            cls._form.install_hook(
                'Auto S PythonFormPRIVATEx;'
            )
        return cls._form

    def __init__(self, num=0, den=None, check=True):
        """Construct a rational function."""
        self.get_instance()  # Ensure self._form

        if isinstance(num, RationalFunction) and den is None:
            self._num = Polynomial(num._num, False)
            self._den = Polynomial(num._den, False)
            return

        if den is None:
            self._num = Polynomial(num, check)
            self._den = Polynomial(1, False)
            if not check:
                # We can skip the canonicalization.
                return
        else:
            self._num = Polynomial(num, check)
            self._den = Polynomial(den, check)
            if check:
                if len(self._den) == 0:
                    raise ZeroDivisionError('({0})/(0)'.format(self._num))

        if check:
            # Ensure that the numerator and denominator are polynomials with
            # integer coefficients.
            # NOTE: content_ bug (vermaseren/form#185).
            self._form.write((
                '#if termsin({0})\n'
                '#$t1={0}*PythonFormPRIVATEx;\n'
                '#$t1=content_($t1)/PythonFormPRIVATEx;\n'
                '#{0}={0}/$t1;\n'
                '#else\n'
                '#$t1=1;\n'
                '#endif\n'
                '#if termsin({1})\n'
                '#$t2={1}*PythonFormPRIVATEx;\n'
                '#$t2=content_($t2)/PythonFormPRIVATEx;\n'
                '#{1}={1}/$t2;\n'
                '#else\n'
                '#$t2=1;\n'
                '#endif\n'
                '#$t=$t1/$t2;\n'
                '#$t1=$t*den_;\n'
                '#inside $t1\n'
                'id 1/PythonFormPRIVATEx?=1;\n'
                '#endinside\n'
                '#$t2=$t1/$t;\n'
                '#{0}={0}*$t1;\n'
                '#{1}={1}*$t2;'
            ).format(self._num._id, self._den._id))

            # Divide the numerator and denominator by their GCD.
            # NOTE: gcd_ bug (vermaseren/form#191).
            self._form.write((
                '#if termsin({0})\n'
                '#$t=gcd_({0},{1});\n'
                '#{0}=div_({0},$t);\n'
                '#{1}=div_({1},$t);\n'
                '#endif'
            ).format(self._num._id, self._den._id))

        # Canonicalize them such that the first term in the denominator has
        # a positive coefficient. If the numerator is 0, then go to the special
        # forms: 0/1 or 0/0.
        self._form.write((
            '#if termsin({0})\n'
            '#$t1=firstterm_({1});\n'
            '#$t2=1;\n'
            '#inside $t1\n'
            '$t2=coeff_;\n'
            '#endinside\n'
            '#$t=theta_(-$t2);\n'
            '#if termsin($t)\n'
            '#{0}=-{0};\n'
            '#{1}=-{1};\n'
            '#endif\n'
            '#else\n'
            '#if termsin({1})\n'
            '#{1}=1;\n'
            '#endif\n'
            '#endif'
        ).format(self._num._id, self._den._id))

    @property
    def num(self):
        """Return the numerator."""
        return self._num

    @property
    def den(self):
        """Return the denominator."""
        return self._den

    def __str__(self):
        """Informal string representation."""
        if not self._den:
            raise ZeroDivisionError('({0})/(0)'.format(self._num))

        if self._den == 1:
            return str(self._num)

        num_str = str(self._num)
        den_str = str(self._den)
        if len(self._num) > 2 or not is_signed_integer(num_str):
            num_str = '({0})'.format(num_str)
        if len(self._den) > 2 or not is_unsigned_integer(den_str):
            den_str = '({0})'.format(den_str)
        return '{0}/{1}'.format(num_str, den_str)

    def __repr__(self):
        """Formal string representation."""
        return "RationalFunction('{0}', '{1}')".format(
            str(self._num), str(self._den))

    def __pos__(self):
        """Return + self.

        Examples
        --------
        >>> p = RationalFunction('1+x', '1-x')
        >>> + p
        RationalFunction('1+x', '1-x')

        """
        return self

    def __neg__(self):
        """Return - self.

        Examples
        --------
        >>> p = RationalFunction('1+x', '1-x')
        >>> - p
        RationalFunction('-1-x', '1-x')

        """
        return RationalFunction(
            '-{0}'.format(self._num._id),
            '{0}'.format(self._den._id),
            False
        )

    def __add__(self, other):
        """Return self + other."""
        if isinstance(other, RationalFunction):
            # NOTE: gcd_ bug (vermaseren/form#191).
            self._form.write((
                '#if termsin({1})\n'
                '#$t=gcd_({1},{3});\n'
                '#else\n'
                '#$t=1;\n'
                '#endif\n'
                '#$t1=div_({1},$t);\n'
                '#$t2=div_({3},$t);\n'
                '#$t1={0}*$t2+{2}*$t1;\n'
                '#$t2={1}*$t2;\n'
                '#if termsin($t1)\n'
                '#$t=gcd_($t1,$t2);\n'
                '#else\n'
                '#$t=1;\n'
                '#endif'
            ).format(self._num._id, self._den._id,
                     other._num._id, other._den._id))
            return RationalFunction('div_($t1,$t)', 'div_($t2,$t)', False)
        if isinstance(other, Polynomial):
            # NOTE: gcd_ bug (vermaseren/form#191).
            self._form.write((
                '#$t1={0}+{2}*{1};\n'
                '#if termsin($t1)\n'
                '#$t=gcd_($t1,{1});\n'
                '#else\n'
                '#$t=1;\n'
                '#endif'
            ).format(self._num._id, self._den._id, other._id))
            return RationalFunction(
                'div_($t1,$t)',
                'div_({0},$t)'.format(self._den._id),
                False
            )
        if isinstance(other, integer_types):
            # NOTE: gcd_ bug (vermaseren/form#191).
            self._form.write((
                '#$t1={0}+{2}*{1};\n'
                '#if termsin($t1)\n'
                '#$t=gcd_($t1,{1});\n'
                '#else\n'
                '#$t=1;\n'
                '#endif'
            ).format(self._num._id, self._den._id, other))
            return RationalFunction(
                'div_($t1,$t)',
                'div_({0},$t)'.format(self._den._id),
                False
            )
        return NotImplemented

    def __pow__(self, other):
        """Return self ** other."""
        if isinstance(other, integer_types):
            if other >= 0:
                # XXX: possibly encounter 0^0.
                return RationalFunction(
                    '{0}^{1}'.format(self._num._id, other),
                    '{0}^{1}'.format(self._den._id, other),
                    False
                )
            elif other < 0:
                return RationalFunction(
                    '{0}^{1}'.format(self._den._id, -other),
                    '{0}^{1}'.format(self._num._id, -other),
                    False
                )
        return NotImplemented
