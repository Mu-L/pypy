import pypy._py as py
from rpython.rtyper.tool.rffi_platform import CompilationError


class BaseAppTest:
    spaceconfig = dict(usemodules=['_continuation'], continuation=True)

    def setup_class(cls):
        try:
            import rpython.rlib.rstacklet
        except CompilationError, e:
            py.test.skip("cannot import rstacklet: %s" % e)

