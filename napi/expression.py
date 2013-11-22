import ast

class NExpression(object):

    def __init__(self):

        self._which = self._shape = None


    def __getattr__(self, name):

        pass

    def __call__(self, sc=False):

        self._indices = None
        self._sc = sc
        return self

    def And(self, values):

        print('And(values={})'.format(values))

    def Or(self, values):

        print('Or(values={})'.format(values))

    def BinOp(self, left, op, right):

        print('> BinOp(left={}, op={}, right={})'.format(left, op, right))

    def Compare(self, left, ops, operands):

        print('> Compare(left={}, ops={}, operands={})'.format(left, ops, operands))

    def UnaryOp(self, op, operand):

        print('> UnaryOp(op={}, operand={})'.format(op, operand))

from ast import Attribute, Call, Name, List, Load, Str
from ast import copy_location, fix_missing_locations

class NewTransformer(ast.NodeTransformer):


    def __init__(self, **kwargs):

        self._e = kwargs.pop('e', '_E')
        self._t = False
        self._kw = []
        self._attrs = {}

    def __getitem__(self, attr):

        return self._attrs.setdefault(attr,
            fix_missing_locations(Attribute(value=fix_missing_locations(Name(id=self._e, ctx=Load())),
                                            attr=attr, ctx=Load())))



    #def visit(self):

    #    self._sc = False
    #    self._t = False

    def visit_BoolOp(self, node):

        t = not self._t

        if t:
            self._t = True
            print('start transforming')
        #print '\t' + ast.dump(node)
        self.generic_visit(node)
        func = self[node.op.__class__.__name__]
        args = [List(elts=node.values, ctx=Load())]
        if t:
            print('stop transforming')
            self._t = False
        return fix_missing_locations(copy_location(Call(func=func, args=args, keywords=self._kw), fix_missing_locations(node)))

    def visit_BinOp(self, node):

        self.generic_visit(node)
        if self._t:
            print('transforming BinOp')
        #print ast.dump(node)
        func = self['BinOp']#node.op.__class__.__name__]
        args = [List(elts=[node.left, Str(node.op.__class__.__name__),
                           node.right], ctx=Load())]
        return fix_missing_locations(copy_location(Call(func=func, args=args, keywords=self._kw), fix_missing_locations(node)))

    def visit_UnaryOp(self, node):

        self.generic_visit(node)
        if self._t:
            print('transforming UnaryOp')
        #print ast.dump(node)
        func = self['UnaryOp']#node.op.__class__.__name__]
        args = [List(elts=[node.op, node.operand], ctx=Load())]
        return fix_missing_locations(copy_location(Call(func=func, args=args, keywords=self._kw), fix_missing_locations(node)))

    def visit_Compare(self, node):

        self.generic_visit(node)
        if self._t:
            print('transforming Compare')
        #print ast.dump(node)
        func = self['Compare']
        args = [node.left,
                List(elts=[Str(op.__class__.__name__)
                           for op in node.ops], ctx=Load()),
                List(elts=node.comparators, ctx=Load())]
        return fix_missing_locations(copy_location(Call(func=func, args=args, keywords=self._kw), fix_missing_locations(node)))
