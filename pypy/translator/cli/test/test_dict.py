from pypy.translator.cli.test.runtest import check


def test_dict():
    def func(x, y):
        d = {x: x+1, y: y+1}
        return d[x]
    check(func, [int, int], (42, 13))
