

def neval(expression, globals=None, locals=None, **kwargs):
    """Evaluate *expression* using *globals* and *locals* dictionaries as
    *global* and *local* namespace.  If *globals* is not given, :func:`globals`
    will be used to get *global* namespace. *expression* will be transformed
    using napi abstract syntax tree :class:`.Transformer`."""

    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins

    from ast import parse
    from ast import fix_missing_locations as fml

    try:
        transformer = kwargs['transformer']
    except KeyError:
        from napi.transformers import Transformer as transformer

    #try:
    node = parse(expression, '<string>', 'eval')
    #except ImportError:
    #    builtins.eval(expression)
    #else:
    if globals is None:
        globals = builtins.globals()
    if locals is None:
        locals = {}
    trans = transformer(globals=globals, locals=locals, **kwargs)
    trans.visit(node)
    code = compile(fml(node), '<string>', 'eval')
    return builtins.eval(code, globals, locals)


def nexec(statement, globals=None, locals=None, **kwargs):
    """Evaluate *statement* using *globals* and *locals* dictionaries as
    *global* and *local* namespace.  If *globals* is not given, :func:`globals`
    will be used to get *global* namespace.  *statement* will be transformed
    using napi abstract syntax tree :class:`.Transformer`."""

    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins

    from ast import parse
    from napi.transformers import Transformer
    from ast import fix_missing_locations as fml
    try:
        node = parse(statement, '<string>', 'exec')
    except ImportError:#KeyError:
        exec(statement)
    else:
        if globals is None:
            globals = builtins.globals()
        if locals is None:
            locals = {}
        trans = Transformer(globals=globals, locals=locals, **kwargs)
        trans.visit(node)
        code = compile(fml(node), '<string>', 'exec')
        return builtins.eval(code, globals, locals)
