from IPython.core.magic import Magics, magics_class, line_magic
from IPython import get_ipython

from .transformers import LazyTransformer

__all__ = ['NapiMagics']


@magics_class
class NapiMagics(Magics):

    """Magic for automatic transformation of abstract syntax trees.

    """

    _state = False
    _config = {'squeeze': False}
    _states = {'off': 0, '0': 0, 'on': 1, '1': 1}
    _validate = {'squeeze': lambda arg: arg in _states}
    _prefix = '_'

    @line_magic
    def napi(self, line):
        """Control the automatic transformation of abstract syntax trees.

        Call as ``%napi on``, ``%napi 1``, ``%napi off`` or ``%napi 0``.
        If called without an argument it works as a toggle.

        """

        args = line.strip().lower().split()


        if args:
            arg = args[0]
            if len(args) == 1 and arg in self._states:
                self._state = self._states[arg]
                msg = 'napi transformer is turned {}'.format(
                    ('OFF', 'ON')[self._state])
            elif arg in self._config:
                if arg == 'squeeze':
                    if len(args) == 1:
                        self._config[arg] = not self._config[arg]
                    elif len(args) == 2:
                        try:
                            self._config['squeeze'] = self._states[args[1]]
                        except KeyError:
                            print('Invalid napi argument: {}.'.format(arg))
                            return
                    else:
                        print('Incorrect number of napi arguments.')
                        return

                    state = ('OFF', 'ON')[self._config['squeeze']]
                    msg = 'napi array squeezing is turned {}'.format(state)
                    self.napi('on')
            else:
                print('Invalid napi argument: {}.'.format(arg))
                return
        else:
            self._state = not self._state
            msg = 'napi transformer is turned {}'.format(
                ('OFF', 'ON')[self._state])

        if self._state:
            self._append()
        else:
            self._remove()

        print(msg)

        # alternatively, but message is not printed at default log level
        if False:
            import logging
            ip_logger = logging.getLogger('TerminalIPythonApp')
            ip_logger.info(msg)


    def _append(self):

        self._remove()
        ip = get_ipython()

        from napi.transformers import napi_compare, napi_and, napi_or
        prefix = self._prefix
        ip.user_global_ns[prefix + 'napi_compare'] = napi_compare
        ip.user_global_ns[prefix + 'napi_or'] = napi_or
        ip.user_global_ns[prefix + 'napi_and'] = napi_and

        ip.ast_transformers.append(LazyTransformer(prefix=prefix,
                                                   **self._config))

    def _remove(self):

        ip = get_ipython()
        ip.ast_transformers = [t for t in ip.ast_transformers
                               if not isinstance(t, LazyTransformer)]
