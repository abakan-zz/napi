"""A New API for simplifying logical operations and comparisons of arrays.

>>> from napi import *
>>> exec(nsource)
>>> neval
<function __main__.neval>

:func:`.neval` function that behaves similar to :func:`eval` handles
chained comparisons and logical operations of arrays delicately:

>>> a = arange(8)
>>> v('2 <= a < 3 or a > 5')
array([ True,  True,  True, False, False, False,  True,  True], dtype=bool)"""

import os
import imp

from .functions import *

from .transformers import *
from . import transformers

__all__ = ['nsource', 'nexec', 'neval'] + transformers.__all__

__version__ = '0.1'

class String(str):

    def __call__(self, neval='neval', nexec='nexec'):

        neval = ' {}('.format(neval)
        nexec = ' {}('.format(nexec)
        return self.replace(' neval(', neval).replace('nexec', nexec)

nsource = String(open(os.path.join(imp.find_module('napi')[1],
                                  'functions.py')).read())


def register_magic():

    from .magics import NapiMagics
    ip = get_ipython()
    if ip is not None:
        ip.register_magics(NapiMagics(ip))

try:
    from IPython import get_ipython
except ImportError:
    pass
else:
    register_magic()