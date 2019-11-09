import pytest

def test_toplevel_annotation():
    # exec because this needs to be in "top level" scope
    exec("""if True:
        a: int
        assert __annotations__['a'] == int
    """)

def test_toplevel_invalid():
    exec("""if True:
        with pytest.raises(NameError):
            a: invalid
    """)

def test_non_simple_annotation():
    class C:
        (a): int
        assert "a" not in __annotations__

def test_simple_with_target():
    class C:
        a: int = 1
        assert __annotations__["a"] == int
        assert a == 1

def test_attribute_target():
    class C:
        a = 1
        a.x: int
        assert __annotations__ == {}

def test_subscript_target():
    # ensure that these type annotations don't raise exceptions
    # during compilation
    class C:
        a = 1
        a[0]: int
        a[1:2]: int
        a[1:2:2]: int
        a[1:2:2, ...]: int
        assert __annotations__ == {}

def test_class_annotation():
    class C:
        a: int
        b: str
        assert "__annotations__" in locals()
    assert C.__annotations__ == {"a": int, "b": str}

def test_unevaluated_name():
    class C:
        def __init__(self):
            self.x: invalid_name = 1
            assert self.x == 1
    C()

def test_nonexistent_target():
    try:
        # this is invalid because `y` is undefined
        # it should raise a NameError
        y[0]: invalid
    except NameError:
        ...

def test_non_simple_func_annotation():
    a = 5
    def f():
        (a): int
        return a
    assert f() == 5

def test_repeated_setup():
    # each exec will run another SETUP_ANNOTATIONS
    # we want to confirm that this doesn't blow away
    # the previous __annotations__
    d = {}
    exec('a: int', d)
    exec('b: int', d)
    exec('assert __annotations__ == {"a": int, "b": int}', d)

def test_function_no___annotations__():
    a: int
    assert "__annotations__" not in locals()

def test_unboundlocal():
    # a simple variable annotation implies its target is a local
    a: int
    with pytest.raises(UnboundLocalError):
        print(a)

def test_ternary_expression_bug():
    class C:
        var: bool = True if False else False
        assert var is False
    assert C.__annotations__ == {"var": bool}

def test_reassigned___annotations__():
    class C:
        __annotations__ = None
        with pytest.raises(TypeError):
            a: int

def test_locals_arent_dicts():
    class O:
        def __init__(self):
            self.dct = {}

        def __getitem__(self, name):
            return self.dct[name]

        def __setitem__(self, name, value):
            self.dct[name] = value

    # don't crash if locals aren't just a normal dict
    exec("a: int; assert __annotations__['a'] == int", {}, O())

def test_NameError_if_annotations_are_gone():
    with pytest.raises(NameError):
        class A:
            del __annotations__
            a: int

def test_lineno():
    s = """

a: int
    """
    c = compile(s, "f", "exec")
    assert c.co_firstlineno == 3

def test_scoping():
    def f(classvar):
        class C:
            cls: classvar = 23
        assert C.__annotations__ == {"cls": "abc"}

    f("abc")