napi - for simplifying array operations
=======================================

*napi* is an abstract syntax tree transformer that let's
evaluation of chained comparisons and logical operations
of NumPy_ arrays to work:

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
using *pip*::

  $ pip install napi

Contents
---------

.. toctree::
   :maxdepth: 2

   tutorial
   reference/index


Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

