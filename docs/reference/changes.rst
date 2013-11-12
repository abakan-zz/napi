Changes
===============================================================================

0.2.1 (Nov 12, 2013)
-------------------------------------------------------------------------------

**New features**:

  * Added automatic array squeezing feature that allows logical operations of
    arrays that can be squeezed into a common shape:

    .. ipython:: python

       from numpy import *
       import napi

    .. ipython:: python
       :suppress:

       napi.register_magic()

    .. ipython:: python

       %napi squeeze

    .. ipython:: python

       ones(10, bool) or zeros((1, 10, 1), bool)



0.2 (Nov 11, 2013)
-------------------------------------------------------------------------------

**New features**:

  * Initial implementation of :func:`.neval`, :func:`.nexec` that behave like
    :func:`eval` and :func:`exec` are available.

**Bug fixes**:

  * Fixed installation problem due to missing :file:`README.rst` in the
    package.