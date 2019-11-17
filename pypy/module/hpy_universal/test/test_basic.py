from .support import HPyTest

class AppTestBasic(HPyTest):
    spaceconfig = {'usemodules': ['hpy_universal']}
    def test_import(self):
        import hpy_universal

    def test_empty_module(self):
        import sys
        mod = self.make_module("""
            @INIT
        """)
        assert type(mod) is type(sys)

    def test_empty_module_initialization(self):
        skip("FIXME")
        import sys
        mod = self.make_module("""
            @INIT
        """)
        assert type(mod) is type(sys)
        assert mod.__loader__.name == 'mytest'
        assert mod.__spec__.loader is mod.__loader__
        assert mod.__file__

    def test_different_name(self):
        mod = self.make_module("""
            @INIT
        """, name="foo")
        assert mod.__name__ == "foo"

    def test_noop_function(self):
        mod = self.make_module("""
            HPy_FUNCTION(f)
            static HPy f_impl(HPyContext ctx, HPy self, HPy args)
            {
                return HPyNone_Get(ctx);
            }
            @EXPORT f METH_NOARGS
            @INIT
        """)
        assert mod.f() is None

    def test_self_is_module(self):
        mod = self.make_module("""
            HPy_FUNCTION(f)
            static HPy f_impl(HPyContext ctx, HPy self, HPy args)
            {
                return HPy_Dup(ctx, self);
            }
            @EXPORT f METH_NOARGS
            @INIT
        """)
        assert mod.f() is mod

    def test_identity_function(self):
        mod = self.make_module("""
            HPy_FUNCTION(f)
            static HPy f_impl(HPyContext ctx, HPy self, HPy arg)
            {
                return HPy_Dup(ctx, arg);
            }
            @EXPORT f METH_O
            @INIT
        """)
        x = object()
        assert mod.f(x) is x
