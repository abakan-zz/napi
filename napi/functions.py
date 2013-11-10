

def neval(expression, globals=None, locals=None, **kwargs):
    """Evaluate *expression* using *globals* and *locals* dictionaries as
    *global* and *local* namespace.  *expression* is transformed using
    :class:`.NapiTransformer`."""

    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins

    from ast import parse
    from ast import fix_missing_locations as fml

    try:
        transformer = kwargs['transformer']
    except KeyError:
        from napi.transformers import NapiTransformer as transformer

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
    """Execute *statement* using *globals* and *locals* dictionaries as
    *global* and *local* namespace.  *statement* is transformed using
    :class:`.NapiTransformer`."""

    try:
        import __builtin__ as builtins
    except ImportError:
        import builtins

    from ast import parse
    from napi.transformers import NapiTransformer
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
        trans = NapiTransformer(globals=globals, locals=locals, **kwargs)
        trans.visit(node)
        code = compile(fml(node), '<string>', 'exec')
        return builtins.eval(code, globals, locals)
