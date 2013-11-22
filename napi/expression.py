import ast
import operator

from ast import Attribute, Call, List, Load, Name, Num, Str, keyword
from ast import copy_location, fix_missing_locations as fml

import numpy
from numpy import ndarray

_setdefault = {}.setdefault
ZERO = lambda dtype: _setdefault(dtype, numpy.zeros(1, dtype)[0])

OPMAP = {
    'Add': operator.add,
    'Sub': operator.sub,
    'Mult': operator.mul,
    'Div': operator.div,
    'Mod': operator.mod,
    'Pow': operator.pow,
    'LShift': operator.lshift,
    'RShift': operator.rshift,
    'BitOr': operator.or_,
    'BitXor': operator.xor,
    'BitAnd': operator.and_,
    'FloorDiv': operator.floordiv,

    'Eq': operator.eq,
    'NotEq': operator.ne,
    'Lt': operator.lt,
    'LtE': operator.le,
    'Gt': operator.gt,
    'GtE': operator.ge,

    'Not': operator.not_
}

END = keyword(arg='end', value=Num(1))

def short_circuit_or(arrays, shape):

    a = arrays.pop(0)
    z = ZERO(a.dtype)
    nz = (a == z).nonzero()
    if len(nz) > 1:
        while arrays:
            a = arrays.pop()
            which = a[nz] == ZERO(a.dtype)
            nz = tuple(i[which] for i in nz)
    else:
        nz = nz[0]
        while arrays:
            a = arrays.pop()[nz]
            nz = nz[a == ZERO(a.dtype)]
    result = numpy.ones(shape, bool)
    result[nz] = False
    return result

def short_circuit_and(arrays, shape):

    a = arrays.pop(0)
    nz = (a if a.dtype == bool else a.astype(bool)).nonzero()
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
    result = numpy.zeros(shape, bool)
    result[nz] = True
    return result

class NExpression(object):

    def __init__(self, **kwargs):

        self._sc = kwargs.get('sc', kwargs.get('shortcircuit', 0))
        self._sq = kwargs.get('sq', kwargs.get('squeeze', False))

        self._which = self._shape = None


    def And(self, values, id=None, **kwargs):

        print('@> And(values={}, id={}, **kwargs={})'.format(values, id, kwargs))

        arrays = []
        result = None
        shapes = set()

        for value in values:
            if isinstance(value, ndarray) and value.shape:
                arrays.append(value)
                shapes.add(value.shape)
            elif not value:
                result = value

        if len(shapes) > 1 and self._sq:
            shapes.clear()
            for i, a in enumerate(arrays):
                a = arrays[i] = a.squeeze()
                shapes.add(a.shape)
            if len(shapes) > 1:
                raise ValueError('array shape mismatch, even after squeezing')

        if len(shapes) > 1:
            raise ValueError('array shape mismatch')

        shape = shapes.pop() if shapes else None

        if result is not None:
            if shape:
                return numpy.zeros(shape, bool)
            else:
                return result
        elif arrays:
            if self._sc and numpy.prod(shape) >= self._sc:
                return short_circuit_and(arrays, shape)
            elif len(arrays) == 2:
                return numpy.logical_and(*arrays)
            else:
                return numpy.all(arrays, 0)
        else:
            return value


    def Or(self, values, id=None, **kwargs):

        print('@> Or(values={}, id={}, **kwargs={})'.format(values, id, kwargs))
        arrays = []
        result = None
        shapes = set()

        for value in values:
            if isinstance(value, ndarray) and value.shape:
                arrays.append(value)
                shapes.add(value.shape)
            elif value:
                result = value

        if len(shapes) > 1 and kwargs.get('squeeze', kwargs.get('sq', False)):
            shapes.clear()
            for i, a in enumerate(arrays):
                a = arrays[i] = a.squeeze()
                shapes.add(a.shape)
            if len(shapes) > 1:
                raise ValueError('array shape mismatch, even after squeezing')

        if len(shapes) > 1:
            raise ValueError('array shape mismatch')

        shape = shapes.pop() if shapes else None

        if result is not None:
            if shape:
                return numpy.ones(shape, bool)
            else:
                return result
        elif arrays:
            if self._sc and numpy.prod(shape) >= self._sc:
                return short_circuit_or(arrays, shape)
            elif len(arrays) == 2:
                return numpy.logical_or(*arrays)
            else:
                return numpy.any(arrays, 0)
        else:
            return value

    def BinOp(self, left, op, right, id=None):

        print('@> BinOp(left={}, op={}, right={}, id={})'.format(left, op, right, id))
        return OPMAP[op](left, right)

    def Compare(self, left, ops, comparators, id=None):

        print('@> Compare(left={}, ops={}, comparators={}, id={})'.format(left, ops, comparators, id))

        values = []
        for op, right in zip(ops, comparators):
            value = OPMAP[op](left, right)
            values.append(value)
            left = right
        if len(values) == 1:
            return values[0]
        else:
            return self.And(values)

    def UnaryOp(self, op, operand, id=None):

        print('@> UnaryOp(op={}, operand={})'.format(op, operand))
        return OPMAP[op](operand)


class NewTransformer(ast.NodeTransformer):


    def __init__(self, **kwargs):

        self._e = kwargs.pop('e', '_E')
        self._t = False
        self._i = 0
        self._id = None
        self._attrs = {}
        self._kw = []

    def __getitem__(self, attr):

        return self._attrs.setdefault(attr,
            fml(Attribute(value=fml(Name(id=self._e, ctx=Load())),
                                            attr=attr, ctx=Load())))

    def visit_BoolOp(self, node):

        start = not self._id is not None

        if start:
            self._i += 1
            self._id = Num(self._i)
            print('start transforming')
        self.generic_visit(node)
        func = self[node.op.__class__.__name__]
        args = [List(elts=node.values, ctx=Load()), self._id]
        if start:
            print('stop transforming')
            self._id = None
            kw = self._kw + [END]
        else:
            kw = self._kw
        return fml(copy_location(Call(func=func, args=args, keywords=kw), node))

    def visit_Compare(self, node):

        self.generic_visit(node)
        if self._id is None:
            return node
        else:
            print('~ Compare')
            func = self['Compare']
            args = [node.left,
                    List(elts=[Str(op.__class__.__name__) for op in node.ops], ctx=Load()),
                    List(elts=node.comparators, ctx=Load()), self._id]
            return copy_location(Call(func=func, args=args, keywords=self._kw), node)

    def visit_BinOp(self, node):

        self.generic_visit(node)
        if self._id is None:
            return node
        else:
            print('~ BinOp')
            func = self['BinOp']
            args = [node.left, Str(node.op.__class__.__name__), node.right, self._id]
            return copy_location(Call(func=func, args=args, keywords=self._kw), node)

    def visit_UnaryOp(self, node):

        self.generic_visit(node)
        if self._id is None:
            return node
        else:
            print('~ UnaryOp')
            func = self['UnaryOp']
            args = [Str(node.op.__class__.__name__), node.operand, self._id]
            return copy_location(Call(func=func, args=args, keywords=self._kw), node)


if __name__ == '__main__':

    reload(exp); _E = exp.NExpression(); t = exp.NewTransformer(); eval(compile(t.visit(ast.parse('[] or not 1 and 2 + 0 < 3', '', 'eval')), '', 'eval'))