python-form
===========

.. image:: https://badge.fury.io/py/python-form.svg
    :target: https://pypi.python.org/pypi/python-form
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/python-form.svg
    :target: https://pypi.python.org/pypi/python-form
    :alt: Python versions

.. image:: https://travis-ci.org/tueda/python-form.svg?branch=master
    :target: https://travis-ci.org/tueda/python-form
    :alt: Build Status

.. image:: https://coveralls.io/repos/tueda/python-form/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/tueda/python-form?branch=master
    :alt: Coverage

.. image:: https://readthedocs.org/projects/python-form/badge/?version=latest
    :target: https://python-form.readthedocs.io/en/latest
    :alt: Documentation Status

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.1044010.svg
    :target: https://doi.org/10.5281/zenodo.1044010
    :alt: DOI

This package provides a mechanism to embed FORM_ [1]_ [2]_ [3]_ programs in
Python code. The basic idea of the implementation is the same as FormLink_ [4]_:
it utilizes unnamed pipes between FORM and an external program [5]_, Python in
this case. It is expected to work on Unix-like systems.

Installation
------------

::

    $ pip install python-form

or directly from GitHub for the latest development version:

::

    $ pip install git+https://github.com/tueda/python-form.git

See also the documentation for `pip install`_.

Example
-------

.. code:: python

    import form

    with form.open() as f:
        f.write('''
            AutoDeclare Vector p;
            Local F = g_(0,p1,...,p6);
            trace4,0;
            .sort
        ''')
        print(f.read('F'))

Documentation
-------------

- `Package Documentation`_
- CHANGELOG_

Licence
-------

python-form is distributed under the MIT licence.
See the LICENCE_ file.

Note that FORM itself adopts the GPL version 3. A program/package using FORM via
python-form could be considered as an aggregate (at your own risk) or a combined
work affected by the GPL.

References
----------

.. _FORM: https://www.nikhef.nl/~form/
.. _FormLink: https://www.feyncalc.org/formlink/
.. _pip install: https://pip.pypa.io/en/stable/reference/pip_install/
.. _Package Documentation: https://python-form.readthedocs.io/en/stable/
.. _CHANGELOG: https://github.com/tueda/python-form/blob/master/CHANGELOG.md
.. _LICENCE: https://github.com/tueda/python-form/blob/master/LICENCE.md

.. [1] J.A.M. Vermaseren,
       New features of FORM,
       `arXiv:math-ph/0010025
       <https://arxiv.org/abs/math-ph/0010025>`_.
.. [2] J. Kuipers, T. Ueda, J.A.M. Vermaseren and J. Vollinga,
       FORM version 4.0,
       `Comput.Phys.Commun. 184 (2013) 1453-1467
       <https://dx.doi.org/10.1016/j.cpc.2012.12.028>`_,
       `arXiv:1203.6543 [cs.SC]
       <https://arxiv.org/abs/1203.6543>`_.
.. [3] https://github.com/vermaseren/form
.. [4] Feng Feng and Rolf Mertig,
       FormLink/FeynCalcFormLink : Embedding FORM in Mathematica and FeynCalc,
       `arXiv:1212.3522 [hep-ph]
       <https://arxiv.org/abs/1212.3522>`_.
.. [5] M. Tentyukov and J.A.M. Vermaseren,
       Extension of the functionality of the symbolic program FORM by external software,
       `Comput.Phys.Commun. 176 (2007) 385-405
       <https://dx.doi.org/10.1016/j.cpc.2006.11.007>`_,
       `arXiv:cs/0604052
       <https://arxiv.org/abs/cs/0604052>`_.
