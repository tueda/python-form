python-form
===========

A Python package for communicating with FORM.

.. image:: https://travis-ci.org/tueda/python-form.svg?branch=master
    :target: https://travis-ci.org/tueda/python-form

.. image:: https://coveralls.io/repos/tueda/python-form/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/tueda/python-form?branch=master

This package provides a mechanism to embed FORM_ [1]_ [2]_ [3]_ programs in
Python code. The basic idea of the implementation is the same as FormLink_ [4]_:
it utilizes unnamed pipes between FORM and an external program [5]_. It is
expected to work on Unix-like systems.

Installation
------------

::

    $ pip install python-form

or directly from GitHub:

::

    $ pip install git+https://github.com/tueda/python-form.git

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

References
----------

.. _FORM: http://www.nikhef.nl/~form/
.. _FormLink: http://www.feyncalc.org/formlink/
.. [1] J.A.M. Vermaseren,
       New features of FORM,
       `arXiv:math-ph/0010025
       <http://arxiv.org/abs/math-ph/0010025>`_.
.. [2] J. Kuipers, T. Ueda, J.A.M. Vermaseren and J. Vollinga,
       FORM version 4.0,
       `Comput.Phys.Commun. 184 (2013) 1453-1467
       <http://dx.doi.org/10.1016/j.cpc.2012.12.028>`_,
       `arXiv:1203.6543 [cs.SC]
       <http://arxiv.org/abs/1203.6543>`_.
.. [3] https://github.com/vermaseren/form
.. [4] Feng Feng and Rolf Mertig,
       FormLink/FeynCalcFormLink : Embedding FORM in Mathematica and FeynCalc,
       `arXiv:1212.3522 [hep-ph]
       <http://arxiv.org/abs/1212.3522>`_.
.. [5] M. Tentyukov and J.A.M. Vermaseren,
       Extension of the functionality of the symbolic program FORM by external software,
       `Comput.Phys.Commun. 176 (2007) 385-405
       <http://dx.doi.org/10.1016/j.cpc.2006.11.007>`_,
       `arXiv:cs/0604052
       <http://arxiv.org/abs/cs/0604052>`_.
