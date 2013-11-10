from IPython.core.magic import Magics, magics_class, line_magic
from IPython import get_ipython

from .transformers import LazyTransformer

__all__ = ['NapiMagics']


@magics_class
class NapiMagics(Magics):

    """Magic for automatic transformation of abstract syntax trees.

    """

    _state = False
    _kwargs = {}
    _states = {'off': 0, '0': 0, 'on': 1, '1': 1}
    _prefix = '_napi_'

    @line_magic
    def napi(self, line):
        """Control the automatic transformation of abstract syntax trees.

        Call as '%napi on', '%napi 1', '%napi off' or '%napi 0'. If called
        without argument it works as a toggle.

        """

        args = line.strip().split()


        if args:
            arg = args[0]
            if len(args) == 1:
                try:
                    self._state = self._states[arg.lower()]
                except KeyError:
                    pass
                    try:
                        self._kwargs[arg] = not self._kwargs[arg]
                    except KeyError:
                        pass
                else:
                    msg = 'napi ast transformer is turned {}'.format(
                        ('OFF', 'ON')[self._state])
            elif False and len(args) == 2:
                if arg in self._kwargs:
                    pass
                else:
                    print('Incorrect napi argument: ' + repr(arg))
                    return
            print('Incorrect napi argument: {}. Use on/1, off/0, '
                  'transformer, or one of {} to configure')
            return


        else:
            self._state = not self._state
            msg = 'napi ast transformer is turned {}'.format(
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

        from napi.transformers import compare, logical_and, logical_or
        prefix = self._prefix
        ip.user_global_ns[prefix + 'compare'] = compare
        ip.user_global_ns[prefix + 'logical_or'] = logical_or
        ip.user_global_ns[prefix + 'logical_and'] = logical_and

        ip.ast_transformers.append(LazyTransformer(prefix=prefix,
                                                   **self._kwargs))

    def _remove(self):

        ip = get_ipython()
        ip.ast_transformers = [t for t in ip.ast_transformers
                               if not isinstance(t, LazyTransformer)]
