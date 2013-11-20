.. image:: https://secure.travis-ci.org/abakan/napi.png?branch=master
   :target: http://travis-ci.org/#!/abakan/napi

napi
====

napi is an abstract syntax tree transformer to simplify NumPy_ array
operations.  In IPython, for example, you can use the following magic:

.. code-block:: ipython

   In [1]: import napi

   In [2]: %napi
   napi ast transformer is turned ON

to enable evaluation of the following expression:

.. code-block:: ipython

   In [3] from numpy import *

   In [4] 0 <= arange(6) < 6 and True
   Out[4]: array([ True,  True,  True,  True,  True,  True], dtype=bool)

.. _NumPy: http://www.numpy.org/

Installation
-------------

*napi* works with Python 2.7, 3.2 and later.

::

  $ pip install -U napi


Docs & Source
-------------

 * Docs: http://napi.rtfd.org
 * Source: https://github.com/abakan/napi

License
-------

*napi* is available under MIT License.