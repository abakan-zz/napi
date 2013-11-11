napi - A New API for simplifying array operations
=================================================

Let's say you have a few data arrays of the same size:

.. ipython:: python

   import numpy as np
   size = 10000
   age = np.random.randint(20, 60, size)
   height = np.random.normal(170, 10, size)

and, you want to make comparisons of the following sort:

.. ipython:: python

   170 >= height >= 160 and 25 <= age <= 30


With the following IPython magic:

.. ipython:: python

   import napi

.. ipython:: python
   :suppress:

   napi.register_magic()

.. ipython:: python

   %napi


You can make it work:


.. ipython:: python

   sel1 = 170 >= height >= 160 and 25 <= age <= 30


This is the equivalent of:

.. ipython:: python

   sel2 = np.logical_and(np.logical_and(np.logical_and(
       height >= 160, height <= 170), age >= 25), age <= 30)

   sel3 = np.all([height >= 160, height <= 170, age >= 25, age <= 30], 0)

   all(sel1 == sel2 == sel3)


Alternate usage
---------------

Alternatively, you can:

.. ipython:: python

   from napi import *
   exec(nsource)

This will define :func:`.neval` in your current namespace:

.. ipython:: python

   neval

which behaves like :func:`eval`:

.. ipython:: python

   sel4 = neval('170 >= height >= 160 and 25 <= age <= 30')
   all(sel1 == sel4)

.. toctree::
   :maxdepth: 2
   :hidden:

   napi


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

