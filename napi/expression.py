import ast
import operator

from ast import AST, Attribute, Call, List, Load, Name, Num, Str
from ast import copy_location as copy, fix_missing_locations as fix
from ast import iter_fields

import numpy
from numpy import ndarray, logical_and, logical_not, logical_or
from numpy import ones, zeros, prod, all as np_all, any as np_any

_setdefault = {}.setdefault
ZERO = lambda dtype: _setdefault(dtype, zeros(1, dtype)[0])
NONE = Name(id='None', ctx=Load())
ROOT = (Num(n=0), Num(n=1))
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
    result = ones(shape, bool)
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
    result = zeros(shape, bool)
    result[nz] = True
    return result

class NExpression(object):
    """
    Expression evaluator.
    """

    def __init__(self, **kwargs):

        self._sc = kwargs.get('sc', kwargs.get('shortcircuit', 0))
        self._sq = kwargs.get('sq', kwargs.get('squeeze', False))
        self._data = {} # uid: (shape, true, false)

    def __getitem__(self, uid):

        return self._data.get(uid, (None, None, None))

    def __delitem__(self, uid):

        self._data.pop(uid, None)

    def And(self, values, uid=None, root=False):

        print('@> And(values={}, uid={}, root={})'.format(values, uid, root))

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
                result = zeros(shape, bool)
            else:
                result = result
        elif arrays:
            if self._sc and prod(shape) >= self._sc:
                result = short_circuit_and(arrays, shape)
            elif len(arrays) == 2:
                result = logical_and(*arrays)
            else:
                result = np_all(arrays, 0)
        else:
            result = value

        if root:
            del self[uid]
        return result


    def Or(self, values, uid=None, root=False):

        print('@> Or(values={}, uid={}, root={})'.format(values, uid, root))
        arrays = []
        result = None
        shapes = set()

        for value in values:
            if isinstance(value, ndarray) and value.shape:
                arrays.append(value)
                shapes.add(value.shape)
            elif value:
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
                result = ones(shape, bool)
            else:
                result = result
        elif arrays:
            if self._sc and prod(shape) >= self._sc:
                result = short_circuit_or(arrays, shape)
            elif len(arrays) == 2:
                result = logical_or(*arrays)
            else:
                result = np_any(arrays, 0)
        else:
            result = value
        if root:
            del self[uid]
        return result

    def BinOp(self, left, op, right, uid=None):

        print('@> BinOp(left={}, op={}, right={}, uid={})'
              .format(left, op, right, uid))
        return OPMAP[op](left, right)

    def Compare(self, left, ops, comparators, uid=None):

        print('@> Compare(left={}, ops={}, comparators={}, uid={})'
              .format(left, ops, comparators, uid))

        values = []
        for op, right in zip(ops, comparators):
            value = OPMAP[op](left, right)
            values.append(value)
            left = right
        if len(values) == 1:
            return values[0]
        else:
            return self.And(values)

    def UnaryOp(self, op, operand, uid=None):

        print('@> UnaryOp(op={}, operand={}, uid={})'
              .format(op, operand, uid))
        if op == 'Not' and isinstance(operand, ndarray):
            return logical_not(operand)
        else:
            return OPMAP[op](operand)


class NewTransformer(ast.NodeTransformer):
    """
    Transforms logical, binary, unary, and comparison operations that are
    within a logical operation or a chained comparison into function calls
    to an instance of :class:`NExpression`.

    >>> import ast
    >>> transform = NewTransformer(e='_E')
    >>> t = transform(ast.parse('a or b'))

    """

    def __init__(self, **kwargs):

        self._e = kwargs.pop('e', '_E')
        self._count = 0
        self._attrs = {}
        self._id = id(self)

    def __getitem__(self, attr):
        """Return :class:`Attribute` instance for :class:`NExpression` methods.
        """

        return self._attrs.setdefault(attr,
            fix(Attribute(value=Name(id=self._e, ctx=Load()),
                                            attr=attr, ctx=Load())))

    @property
    def _uid(self):
        """Unique identifier used for identification of binary, unary,
        comparison, and logical operations that are within a logical
        operation or a chained comparison."""

        self._count += 1
        return Str(s='{}_{}'.format(self._id, self._count))

    def visit(self, node, uid=None):
        """Visit *node* by passing *uid* to the visitor method."""

        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, uid)

    def generic_visit(self, node, uid=None):

        for field, old_value in iter_fields(node):
            old_value = getattr(node, field, None)
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, AST):
                        value = self.visit(value, uid)
                        if value is None:
                            continue
                        elif not isinstance(value, AST):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, AST):
                new_node = self.visit(old_value, uid)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node

    __call__ = visit

    def visit_BoolOp(self, node, uid=None):

        print('~ BoolOp')
        if uid is None:
            root = ROOT[1]
            uid = self._uid
        else:
            root = ROOT[0]
        self.generic_visit(node, uid)
        func = self[node.op.__class__.__name__]
        args = [List(elts=node.values, ctx=Load()), uid, root]
        return fix(copy(Call(func=func, args=args, keywords=[]), node))

    def visit_Compare(self, node, uid=None):
        """Transform a chained comparison *node* or any comparison node
        that is within a logical operation (*uid* is not ``None``)."""

        if uid is None and len(node.comparators) > 1:
            uid = self._uid

        self.generic_visit(node, uid)
        if uid is None:
            return node
        else:
            print('~ Compare')
            func = self['Compare']
            args = [node.left,
                    List(elts=[Str(op.__class__.__name__) for op in node.ops],
                         ctx=Load()),
                    List(elts=node.comparators, ctx=Load()), uid]
            return copy(Call(func=func, args=args, keywords=[]), node)

    def visit_BinOp(self, node, uid=None):
        """Transform binary operation *node* that it is within a logical
        operation or a chained comparison."""

        self.generic_visit(node, uid)
        if uid is None:
            return node
        else:
            print('~ BinOp')
            func = self['BinOp']
            args = [node.left, Str(node.op.__class__.__name__),
                    node.right, uid]
            return copy(Call(func=func, args=args, keywords=[]), node)

    def visit_UnaryOp(self, node, uid=None):
        """Transform logical `not` operation or an unary operation *node* that
        it is within a logical operation or a chained comparison."""

        self.generic_visit(node, uid)
        if uid is None and node.op.__class__.__name__ == 'Not':
            uid = self._uid

        if uid is None:
            return node
        else:
            print('~ UnaryOp')
            func = self['UnaryOp']
            args = [Str(node.op.__class__.__name__), node.operand, uid]
            return fix(copy(Call(func=func, args=args, keywords=[]), node))
