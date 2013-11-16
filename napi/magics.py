from IPython.core.magic import Magics, magics_class, line_magic
from IPython import get_ipython

from .transformers import LazyTransformer

__all__ = ['NapiMagics']

STATES = {'off': 0, '0': 0, 'on': 1, '1': 1}

@magics_class
class NapiMagics(Magics):

    """Magic for automatic transformation of abstract syntax trees.

    """

    _state = False
    _kwargs = {'sq': False, 'sc': 0}
    _option = {'sq': ('sq', 'squeeze',
                      lambda arg: not arg,
                      lambda arg: ('OFF', 'ON')[arg],
                      lambda arg: arg in STATES,
                      lambda arg: bool(STATES[arg])),
               'sc': ('sc', 'shortcircuit',
                       lambda arg: 0 if arg > 0 else 10000,
                       lambda arg: arg,
                       lambda arg: arg.isdigit(), int)}
    _option['squeeze'] = _option['sq']
    _option['shortcircuit'] = _option['sc']
    _prefix = '_'

    @line_magic
    def napi(self, line):
        """Control the automatic transformation of abstract syntax trees.

        Call as ``%napi on``, ``%napi 1``, ``%napi off`` or ``%napi 0``.
        If called without an argument it works as a toggle.

        **Configuration**:

          * ``%napi sc`` or ``%napi shortcircuit`` toggles
            :term:`short-circuiting`.

          * ``%napi sq`` or ``%napi squeeze`` toggles array :term:`squeezing`.
            ``on`` or ``1`` and ``off`` or ``0`` arguments are also recognized.
            """

        args = line.strip().lower().split()

        if args:
            self._config(*args)
        else:
            self._state = not self._state
            msg = 'napi transformer is {}'.format(('OFF', 'ON')[self._state])
            print(msg)

        if self._state:
            self._append()
        else:
            self._remove()


    def _config(self, *args):

        arg = args[0]
        if len(args) == 1 and arg in STATES:
            self._state = STATES[arg]
            print('napi transformer is {}'.format(('OFF', 'ON')[self._state]))
            return
        elif arg in self._option:
            (keyword, verbose, toggle,
                display, validate, convert) = self._option[arg]
            if len(args) == 1:
                self._kwargs[keyword] = value = toggle(self._kwargs[keyword])
                print('napi configured: {} = {}'
                      .format(verbose, display(value)))
                return
            elif len(args) == 2:
                value = args[1]
                if validate(value):
                    self._kwargs[keyword] = value = convert(value)
                    print('napi configured: {} = {}'
                          .format(verbose, display(value)))
                else:
                    print('Invalid napi {} argument: {}'
                          .format(verbose, value))
                return
        print('Invalid napi argument: {}'.format(arg))
        return

    def _append(self):

        self._remove()
        ip = get_ipython()

        from napi.transformers import napi_compare, napi_and, napi_or
        prefix = self._prefix
        ip.user_global_ns[prefix + 'napi_compare'] = napi_compare
        ip.user_global_ns[prefix + 'napi_or'] = napi_or
        ip.user_global_ns[prefix + 'napi_and'] = napi_and

        ip.ast_transformers.append(LazyTransformer(prefix=prefix,
                                                   **self._kwargs))

    def _remove(self):

        ip = get_ipython()
        ip.ast_transformers = [t for t in ip.ast_transformers
                               if not isinstance(t, LazyTransformer)]
