napi - A New API for simplifying array operations
=================================================

Let's say you have a few data arrays of the same size:

.. ipython:: python

   import numpy as np
   size = 10000
   age = np.random.randint(20, 60, size)
   height = np.random.normal(170, 10, size)
   gender = np.random.choice(np.array(list('FM')), size)


And, you want to make comparisons of the following sort:

.. ipython:: python

   gender == "F" and 170 > height > 160 and 25 < age < 30

With the following IPython magic:

.. ipython:: python

   import napi
   %napi


You can make it work:


.. ipython:: python

   sel1 = gender == "F" and 170 >= height >= 160 and 25 <= age <= 30

This is the equivalent of the following:

.. ipython:: python

   sel2 = np.logical_and(np.logical_and(np.logical_and(np.logical_and(
       gender == "F", height >= 160), height <= 170), age >= 25), age <= 30)
   sel3 = np.all([gender == "F", height >= 160, height <= 170,
                  age >= 25, age <= 30], 0)
   print(np.all(sel1 == sel2 == sel3))


Contents:

.. toctree::
   :maxdepth: 2
   :hidden:

   napi


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

