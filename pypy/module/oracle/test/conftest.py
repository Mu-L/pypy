import pypy._py as py
def pytest_runtest_setup():
    py.test.importorskip("pypy.module.oracle.roci")
