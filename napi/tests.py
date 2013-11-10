from nose.tools import raises
import numpy as np

from napi import neval


randbools = lambda *n: np.random.randn(*n) < 0


def check_logicops_of_python_types(source, debug=False):

    result, expect = neval(source, debug=debug), eval(source)
    assert result == expect, '{} != {}'.format(result, expect)


def test_logicops_of_python_types(debug=False):

    for src in [
        '1 and True', 'True and 1', '[] and True', 'True and []', '1 and [1]',
        '0 or True', 'False or 1', '[] or True', 'True or []', 'False or [1]',
        'True and [1] and 1 and {1: 1}',
        'True and [1] and 1 and {1: 1} and {}',
        'True and [1] and 0 or {} and {1: 1}',]:

        yield check_logicops_of_python_types, src, debug


def check_logicops_of_arrays(source, expect, ns, debug=False, sc=10000):

    result = neval(source, ns, debug=debug)
    assert np.all(result == expect), '{} != {}'.format(result, expect)


def test_logicops_of_arrays(debug=False):

    a = np.arange(10)
    b = randbools(10)

    bo = np.ones(10, bool)
    bz = np.zeros(10, bool)

    ns = locals()
    for src, res in [
        ('a and a', np.logical_and(a, a)),
        ('b and b', np.logical_and(b, b)),
        ('b and b and b', np.logical_and(b, b)),
        ('a and b', np.logical_and(a, b)),
        ('a or a', np.logical_or(a, a)),
        ('b or b', np.logical_or(b, b)),
        ('a or b', np.logical_or(a, b)),
        ('a or b or b', np.logical_or(a, b)),
        ('not a', np.logical_not(a)),
        ('not b', np.logical_not(b)),
        ('a and not a', bz),
        ('b and not b', bz),
        ('b and True', b),
        ('(a or b) and False', bz),]:

        yield check_logicops_of_arrays, src, res, ns, debug


def test_array_squeezing(debug=False):


    b = randbools(10)
    b2d = randbools(1, 10)
    b3d = randbools(1, 10, 1)
    b5d = randbools(2, 1, 5, 1, 10)
    b6d = randbools(1, 2, 1, 5, 1, 10, 1)
    ns = locals()
    for src, res in [
        ('b or b2d', np.logical_or(b, b2d.squeeze())),
        ('b or b2d and b3d', np.logical_or(b,
            np.logical_and(b2d.squeeze(), b3d.squeeze()))),
        ('b5d and b6d', np.logical_and(b5d.squeeze(), b6d.squeeze())),
        ]:

        yield check_logicops_of_arrays, src, res, ns, debug




def test_logicops_with_arithmetics_and_comparisons(debug=False):

    a = np.arange(10)
    b = randbools(10)

    ns = locals()
    for src, res in [
        ('a >= 0 and a + 1', np.logical_and(a >= 0, a + 1)),
        ('-a <= 0 and a**2 + 1', np.logical_and(-a <= 0, a**2 + 1)),
        ('---a - 1 <= 0 and b', np.logical_and(---a - 1<= 0, b)),
        ]:

        yield check_logicops_of_arrays, src, res, ns, debug


def test_short_circuiting(debug=False):

    arr = [randbools(10000) for i in range(5)]
    a, b, c, d, e = arr

    ns = locals()
    for sc in (False, 10000):
        for src, res in [
            ('a and a', np.logical_and(a, a)),
            ('b and b', np.logical_and(b, b)),
            ('a and b', np.logical_and(a, b)),
            ('a or a', np.logical_or(a, a)),
            ('b or b', np.logical_or(b, b)),
            ('a or b', np.logical_or(a, b)),
            ('a and b and c and d and e', np.all(arr, 0)),
            ('a or b or c or d or e', np.any(arr, 0)),
            ('a and b or c or d and e',
              np.any([np.logical_and(a, b), c, np.logical_and(d, e)], 0)),
            ]:

            yield check_logicops_of_arrays, src, res, ns, debug, sc

def test_multidim_short_circuiting(debug=False):

    arr = [randbools(10, 100, 10) for i in range(5)]
    a, b, c, d, e = arr

    ns = locals()
    for sc in (False, 10000):
        for src, res in [
            ('a and a', np.logical_and(a, a)),
            ('b and b', np.logical_and(b, b)),
            ('a and b', np.logical_and(a, b)),
            ('a or a', np.logical_or(a, a)),
            ('b or b', np.logical_or(b, b)),
            ('a or b', np.logical_or(a, b)),
            ('a and b and c and d and e', np.all(arr, 0)),
            ('a or b or c or d or e', np.any(arr, 0)),
            ('a and b or c or d and e',
              np.any([np.logical_and(a, b), c, np.logical_and(d, e)], 0)),
            ]:

            yield check_logicops_of_arrays, src, res, ns, debug, sc



def test_comparison_chaining(debug=False):
    """`a < b < c < d`"""

    a = np.arange(10) - 4
    b, c, d = a * 2, a * 3, a * 4

    ns = locals()
    for src, res in [
        ('a < b < c < d', np.all([a < b, b < c, c < d], 0)),
        ('a == b == c == d', np.all([a == b, b == c, c == d], 0)),
        ('0 == a == 0 == b', np.all([a == 0, b == 0,], 0)),
        ]:

        yield check_logicops_of_arrays, src, res, ns, debug


@raises(ValueError)
def check_array_problems(source, ns, debug=False):

    neval(source, ns, debug=debug)


def test_array_problems(debug=False):

    a5 = randbools(5)
    a9 = randbools(9)
    a9by5 = randbools(9, 5)

    ns = locals()
    for src in [
        'a5 and a9',
        'a9 or a5',
        'a9 or a9by5',
        ]:

        yield check_array_problems, src, ns, debug

@raises(NameError)
def test_name_problem(debug=False):

    neval('a and b', {}, debug=debug)


'''


def test_or_not(debug=False):

    a = booleans(10)
    assert all(eval('a or not a', locals(), debug=debug) ==
               any([a, invert(a)], 0))

def test_equal(debug=False):

    a = arange(10)
    assert all(eval('a == 1 and a', locals(), debug=debug) ==
               all([a == 1, a], 0))


'''