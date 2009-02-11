import py
from pypy.rlib.jit import JitDriver, hint
from pypy.jit.hintannotator.policy import StopAtXPolicy
from pyjitpl import get_stats
from pypy.rpython.ootypesystem import ootype
from test.test_basic import LLJitMixin, OOJitMixin


class ListTests:

    def check_all_virtualized(self):
        get_stats().check_loops(new=0, new_with_vtable=0,
                                call__4=0, call__8=0, call_ptr=0)

    def test_simple_array(self):
        def f(n):
            while n > 0:
                lst = [n]
                n = lst[0] - 1
            return n
        res = self.meta_interp(f, [10], exceptions=False)
        assert res == 0
        get_stats().check_loops(int_sub=1)
        self.check_all_virtualized()

    def test_append_pop(self):
        def f(n):
            while n > 0:
                lst = []
                lst.append(5)
                lst.append(n)
                lst[0] -= len(lst)
                three = lst[0]
                n = lst.pop() - three
            return n
        res = self.meta_interp(f, [31], exceptions=False)
        assert res == -2
        self.check_all_virtualized()

    def test_insert(self):
        def f(n):
            while n > 0:
                lst = [1, 2, 3]
                lst.insert(0, n)
                n = lst[0] - 10
            return n
        res = self.meta_interp(f, [33], exceptions=False)
        assert res == -7
        self.check_all_virtualized()

    def test_list_escapes(self):
        def f(n):
            while True:
                lst = []
                lst.append(n)
                n = lst.pop() - 3
                if n < 0:
                    return len(lst)
        res = self.meta_interp(f, [31], exceptions=False)
        assert res == 0
        self.check_all_virtualized()

    def test_list_reenters(self):
        def f(n):
            while n > 0:
                lst = []
                lst.append(n)
                if n < 10:
                    lst[-1] = n-1
                n = lst.pop() - 3
            return n
        res = self.meta_interp(f, [31], exceptions=False)
        assert res == -1
        self.check_all_virtualized()

    def test_cannot_merge(self):
        def f(n):
            while n > 0:
                lst = []
                if n < 20:
                    lst.append(n-3)
                if n > 5:
                    lst.append(n-4)
                n = lst.pop()
            return n
        res = self.meta_interp(f, [30], exceptions=False)
        assert res == -1
        self.check_all_virtualized()

    def test_extend(self):
        def f(n):
            while n > 0:
                lst = [5, 2]
                lst.extend([6, 7, n - 10])
                n = lst.pop()
            return n
        res = self.meta_interp(f, [33], exceptions=False)
        assert res == -7
        self.check_all_virtualized()

    def test_single_list(self):
        py.test.skip("in-progress")
        def f(n):
            lst = [n] * n
            while n > 0:
                n = lst.pop()
                lst.append(n - 10)
            a = lst.pop()
            b = lst.pop()
            return a * b
        res = self.meta_interp(f, [37], exceptions=False)
        assert res == -13 * 37
        self.check_all_virtualized()


class TestOOtype(ListTests, OOJitMixin):
    pass

class TestLLtype(ListTests, LLJitMixin):
    pass
