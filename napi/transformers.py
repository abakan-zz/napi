import ast
import operator

from ast import fix_missing_locations as fml
from ast import copy_location, parse
from _ast import Name, Expression, Num, Str, keyword
from _ast import And, Or, Not, Eq, NotEq, Lt, LtE, Gt, GtE
from _ast import BoolOp, Compare, Subscript, Load, Index, Call, List
from _ast import Dict

import numpy
from numpy import ndarray

__all__ = ['Transformer', 'LazyTransformer']

def ast_name(id, ctx=Load()):

    name = Name(id, ctx)
    name._fields = ('id', 'ctx')
    return name

COMPARE = {
    Eq: operator.eq,
    NotEq: operator.ne,
    Lt: operator.lt,
    LtE: operator.le,
    Gt: operator.gt,
    GtE: operator.ge,
    'Eq': operator.eq,
    'NotEq': operator.ne,
    'Lt': operator.lt,
    'LtE': operator.le,
    'Gt': operator.gt,
    'GtE': operator.ge,
}

ATTRMAP = {
    Num: 'n',
    Str: 's',
}

EVALSET = {List: '',
    Dict: ''
}

RESERVED = {'True': True, 'False': False, 'None': None}


def compare(left, ops, comparators, **kwargs):

    values = []
    for op, right in zip(ops, comparators):
        values.append(COMPARE[op](left, right))
        left = right
    result = logical_and(values)
    if isinstance(result, ndarray):
        return result
    else:
        return bool(result)

def logical_and(values, **kwargs):

    arrays = []
    result = None
    shapes = set()

    for value in values:
        if isinstance(value, ndarray) and value.shape:
            arrays.append(value)
            shapes.add(value.shape)
        elif not value:
            result = value

    if len(shapes) > 1:
        shapes.clear()
        for i, a in enumerate(arrays):
            a = arrays[i] = a.squeeze()
            shapes.add(a.shape)
        if len(shapes) > 1:
            raise ValueError('array shape mismatch, even after squeezing')

    shape = shapes.pop() if shapes else None

    if result is not None:
        if shape:
            return numpy.zeros(shape, bool)
        else:
            return result
    elif arrays:
        if len(arrays) == 2:
            return numpy.logical_and(*arrays)
        else:
            return numpy.all(arrays, 0)
    else:
        return value

def logical_or(values, **kwargs):

    arrays = []
    result = None
    shapes = set()

    for value in values:
        if isinstance(value, ndarray) and value.shape:
            arrays.append(value)
            shapes.add(value.shape)
        elif value:
            result = value

    if len(shapes) > 1:
        shapes.clear()
        for i, a in enumerate(arrays):
            a = arrays[i] = a.squeeze()
            shapes.add(a.shape)
        if len(shapes) > 1:
            raise ValueError('array shape mismatch, even after squeezing')

    shape = shapes.pop() if shapes else None

    if result is not None:
        if shape:
            return numpy.ones(shape, bool)
        else:
            return result
    elif arrays:
        return numpy.any(arrays, 0)
    else:
        return value

class LazyTransformer(ast.NodeTransformer):

    def __init__(self, prefix, **kwargs):

        self._prefix = prefix
        self._kwargs = [keyword(identifier=key, expr=value)
                        for key, value in kwargs]

    def visit_Compare(self, node):

        if len(node.ops) > 1:
            #print ast.dump(node, True, True)
            node = Call(func=Name(id=self._prefix + 'compare', ctx=Load()),
                        args=[node.left,
                              List(elts=[Str(op.__class__.__name__) for op in node.ops], ctx=Load()),
                              List(elts=node.comparators, ctx=Load())],
                        keywords=self._kwargs, starargs=None, kwargs=None)
            fml(node)
            #print ast.dump(node, True, True)
        self.generic_visit(node)
        return node

    def visit_BoolOp(self, node):

        if isinstance(node.op, And):
            call = self._prefix + 'logical_and'
        else:
            call = self._prefix + 'logical_or'
        node = Call(func=Name(id=call, ctx=Load()),
                    args=[List(elts=node.values, ctx=Load())],
                    keywords=self._kwargs, starargs=None, kwargs=None)
        fml(node)
        self.generic_visit(node)
        return node

class Transformer(ast.NodeTransformer):

    def __init__(self, globals={}, locals={}, **kwargs):

        self._g, self._l = globals, locals
        self._ti = 0
        self._kwargs = kwargs
        self._indent = 0
        if False and not kwargs.get('debug', False):
            self._debug = lambda *args, **kwargs: None
        self._sc = kwargs.get('sc', 10000)
        #self._which = None
        self._evaluate = kwargs.get('evaluate', False)
        self._subscript = kwargs.get('subscript')

    def __getitem__(self, node):

        if isinstance(node, Name):
            name = node.id
            try:
                return self._l[name]
            except KeyError:
                try:
                    return self._g[name]
                except KeyError:
                    try:
                        return RESERVED[name]
                    except KeyError:
                        raise NameError('name {} is not defined :)'
                                        .format(repr(name)))
        try:
            return getattr(node, ATTRMAP[node.__class__])
        except KeyError:
            self._debug('_get', node)
            expr = Expression(fml(Transformer(self._g, self._l, **self._kwargs)
                              .visit(node)))
            try:
                return eval(compile(expr, '<string>', 'eval'), self._g, self._l)
            except Exception as err:
                raise err
        if node.__class__ in EVALSET:
            return eval(node)
        else:
            return getattr(node, ATTRMAP[node.__class__])

    def __setitem__(self, name, value):

        self._debug('self[{}] = {}'.format(name ,value))
        if self._subscript:
            self._l[self._subscript][name] = value
        else:
            self._l[name] = value

    def _tn(self):
        """Return a temporary variable name."""

        self._ti += 1
        return '__temp__' + str(self._ti)

    def _incr(self):

        self._indent += 1

    def _decr(self):

        self._indent -= 1

    def _debug(self, *args, **kwargs):

        print((self._indent + kwargs.get('incr', 0)) * '  ' +
              ' '.join(['{}'] * len(args)).format(*args))

    def visit_UnaryOp(self, node):
        """Interfere with ``not`` operation to :func:`numpy.logical_not`."""

        if isinstance(node.op, Not):
            self._debug('UnaryOp', node.op, incr=1)
            operand = self[node.operand]
            self._debug('|-', operand, incr=2)
            tn = self._tn()
            result = numpy.logical_not(operand)
            self._debug('|_', result, incr=2)
            self[tn] = result
            return ast_name(tn)
        else:
            return self.generic_visit(node)

    def visit_Compare(self, node):

        self._debug('Compare', node.ops, incr=1)
        if len(node.ops) > 1:
            values = []
            left = self[node.left]
            for op, right in zip(node.ops, node.comparators):
                right = self[right]
                tn = self._tn()
                value = COMPARE[op.__class__](left, right)
                self[tn] = value
                values.append(ast_name(tn, value))
                left = right
            val = BoolOp(And(), values)
            return self.visit_BoolOp(val)
        self.generic_visit(node)
        return node

    def visit_BoolOp(self, node):
        """Interfere with boolean operations and use :func:`numpy.all` and
        :func:`numpy.any` functions for ``and`` and ``or`` operations.
        *axis* argument to these functions is ``0``."""

        self._incr()
        self._debug('BoolOp', node.op)
        if isinstance(node.op, And):
            result = self._and(node)
        else:
            result = self._or(node)
        self._debug('|_', result, incr=1)
        self._decr()
        return self._return(result, node)

    def _and(self, node):

        arrays = []
        result = None
        shapes = set()

        for item in node.values:
            value = self[item]
            self._debug('|-', value, incr=1)
            if isinstance(value, ndarray) and value.shape:
                arrays.append(value)
                shapes.add(value.shape)
            elif not value:
                result = value

        if len(shapes) > 1:
            shapes.clear()
            for i, a in enumerate(arrays):
                a = arrays[i] = a.squeeze()
                shapes.add(a.shape)
            if len(shapes) > 1:
                raise ValueError('array shape mismatch, even after squeezing')

        shape = shapes.pop() if shapes else None

        if result is not None:
            if shape:
                return numpy.zeros(shape, bool)
            else:
                return result
        elif arrays:
            self._debug('|~ Arrays:', arrays, incr=1)
            if len(arrays) == 2:
                return numpy.logical_and(*arrays)
            if self._sc and numpy.prod(shape) >= self._sc:
                a = arrays.pop(0)
                nz = (a if a.dtype == bool else
                      a.astype(bool)).nonzero()
                if len(nz) > 1:
                    while arrays:
                        a = arrays.pop()[nz]
                        which = a if a.dtype == bool else a.astype(bool)
                        nz = tuple(i[which] for i in nz)
                else:
                    nz = nz[0]
                    while arrays:
                        a = arrays.pop()[nz]
                        nz = nz[a if a.dtype == bool else a.astype(bool)]
                        self._debug('|~ nonzero:', len(nz), incr=2)
                result = numpy.zeros(shape, bool)
                result[nz] = True
                return result
            else:
                return numpy.all(arrays, 0)
        else:
            return value

    def _or(self, node):

        arrays = []
        result = None
        shapes = set()

        for item in node.values:
            value = self[item]
            self._debug('|-', value, incr=1)
            if isinstance(value, ndarray) and value.shape:
                arrays.append(value)
                shapes.add(value.shape)
            elif value:
                result = value

        if len(shapes) > 1:
            shapes.clear()
            for i, a in enumerate(arrays):
                a = arrays[i] = a.squeeze()
                shapes.add(a.shape)
            if len(shapes) > 1:
                raise ValueError('array shape mismatch, even after squeezing')

        shape = shapes.pop() if shapes else None

        if result is not None:
            if shape:
                return numpy.ones(shape, bool)
            else:
                return result
        elif arrays:
            self._debug('|~ Arrays:', arrays, incr=1)
            return numpy.any(arrays, 0)
        else:
            return value

    def _return(self, val, node):

        tn = self._tn()
        if self._subscript:
            self._l['_napi_temp_ns'][tn] = val
            return Subscript(
                value=Name(id=self._subscript, ctx=Load()),
                slice=Index(value=Str(s=tn)),
                ctx=getattr(node, 'ctx', Load()))
        else:
            self[tn] = val
            return ast_name(tn)


    def _default(self, node):

        self._debug('default', node)
        expr = Expression(fml(Transformer(self._g, self._l, **self._kwargs)
                          .visit(node)))
        result = eval(compile(expr, '<string>', 'eval'), self._g, self._l)
        tn = self._tn()
        self[tn] = result
        return ast_name(tn)