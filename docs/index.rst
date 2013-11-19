napi - for simplifying array operations
=======================================

*napi* is an abstract syntax tree transformer that makes
chained comparisons and logical operations of NumPy_ arrays
work:

.. ipython:: python
   :suppress:

   from numpy import *
   import napi
   napi.register_magic()

.. ipython:: python

   %napi

.. ipython:: python

   a = arange(20)
   6 <= a < 16 and a != 10



Installation
------------

*napi* is a lightweight Python package. You can install it
using pip_::

  $ pip install napi

Contents
---------

.. toctree::
   :maxdepth: 2

   tutorial
   reference/index
   whatsnew

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

