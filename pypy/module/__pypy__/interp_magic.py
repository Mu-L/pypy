from pypy.interpreter.error import oefmt, wrap_oserror
from pypy.interpreter.gateway import unwrap_spec
from pypy.interpreter.pycode import CodeHookCache
from pypy.interpreter.pyframe import PyFrame
from pypy.interpreter.mixedmodule import MixedModule
from rpython.rlib.objectmodel import we_are_translated
from pypy.objspace.std.dictmultiobject import W_DictMultiObject
from pypy.objspace.std.listobject import W_ListObject
from pypy.objspace.std.setobject import W_BaseSetObject
from pypy.objspace.std.typeobject import MethodCache
from pypy.objspace.std.mapdict import MapAttrCache
from rpython.rlib import rposix, rgc, rstack


def internal_repr(space, w_object):
    return space.newtext('%r' % (w_object,))


def attach_gdb(space):
    """Run an interp-level gdb (or pdb when untranslated)"""
    from rpython.rlib.debug import attach_gdb
    attach_gdb()


@unwrap_spec(name='text')
def method_cache_counter(space, name):
    """Return a tuple (method_cache_hits, method_cache_misses) for calls to
    methods with the name."""
    assert space.config.objspace.std.withmethodcachecounter
    cache = space.fromcache(MethodCache)
    return space.newtuple([space.newint(cache.hits.get(name, 0)),
                           space.newint(cache.misses.get(name, 0))])

def reset_method_cache_counter(space):
    """Reset the method cache counter to zero for all method names."""
    assert space.config.objspace.std.withmethodcachecounter
    cache = space.fromcache(MethodCache)
    cache.misses = {}
    cache.hits = {}
    cache = space.fromcache(MapAttrCache)
    cache.misses = {}
    cache.hits = {}

@unwrap_spec(name='text')
def mapdict_cache_counter(space, name):
    """Return a tuple (index_cache_hits, index_cache_misses) for lookups
    in the mapdict cache with the given attribute name."""
    assert space.config.objspace.std.withmethodcachecounter
    cache = space.fromcache(MapAttrCache)
    return space.newtuple([space.newint(cache.hits.get(name, 0)),
                           space.newint(cache.misses.get(name, 0))])

def builtinify(space, w_func):
    """To implement at app-level modules that are, in CPython,
    implemented in C: this decorator protects a function from being ever
    bound like a method.  Useful because some tests do things like put
    a "built-in" function on a class and access it via the instance.
    """
    from pypy.interpreter.function import Function, BuiltinFunction
    func = space.interp_w(Function, w_func)
    bltn = BuiltinFunction(func)
    return bltn

def hidden_applevel(space, w_func):
    """Decorator that hides a function's frame from app-level"""
    from pypy.interpreter.function import Function
    func = space.interp_w(Function, w_func)
    func.getcode().hidden_applevel = True
    return w_func

def get_hidden_tb(space):
    """Return the traceback of the current exception being handled by a
    frame hidden from applevel.
    """
    operr = space.getexecutioncontext().sys_exc_info(for_hidden=True)
    return space.w_None if operr is None else operr.get_w_traceback(space)

@unwrap_spec(meth='text')
def lookup_special(space, w_obj, meth):
    """Lookup up a special method on an object."""
    if space.is_oldstyle_instance(w_obj):
        raise oefmt(space.w_TypeError,
                    "this doesn't do what you want on old-style classes")
    w_descr = space.lookup(w_obj, meth)
    if w_descr is None:
        return space.w_None
    return space.get(w_descr, w_obj)

def do_what_I_mean(space, w_crash=None):
    if not space.is_none(w_crash):
        raise ValueError    # RPython-level, uncaught
    return space.newint(42)


def strategy(space, w_obj):
    """ strategy(dict or list or set)

    Return the underlying strategy currently used by a dict, list or set object
    """
    if isinstance(w_obj, W_DictMultiObject):
        name = w_obj.get_strategy().__class__.__name__
    elif isinstance(w_obj, W_ListObject):
        name = w_obj.strategy.__class__.__name__
    elif isinstance(w_obj, W_BaseSetObject):
        name = w_obj.strategy.__class__.__name__
    else:
        raise oefmt(space.w_TypeError, "expecting dict or list or set object")
    return space.newtext(name)

def get_console_cp(space):
    """get_console_cp()

    Return the console and console output code page (windows only)
    """
    from rpython.rlib import rwin32    # Windows only
    return space.newtuple([
        space.newtext('cp%d' % rwin32.GetConsoleCP()),
        space.newtext('cp%d' % rwin32.GetConsoleOutputCP()),
        ])

@unwrap_spec(sizehint=int)
def resizelist_hint(space, w_list, sizehint):
    """ Reallocate the underlying storage of the argument list to sizehint """
    if not isinstance(w_list, W_ListObject):
        raise oefmt(space.w_TypeError, "arg 1 must be a 'list'")
    w_list._resize_hint(sizehint)

@unwrap_spec(sizehint=int)
def newlist_hint(space, sizehint):
    """ Create a new empty list that has an underlying storage of length sizehint """
    return space.newlist_hint(sizehint)

@unwrap_spec(debug=bool)
def set_debug(space, debug):
    space.sys.debug = debug
    space.setitem(space.builtin.w_dict,
                  space.newtext('__debug__'),
                  space.newbool(debug))

@unwrap_spec(estimate=int)
def add_memory_pressure(space, estimate):
    """ Add memory pressure of estimate bytes. Useful when calling a C function
    that internally allocates a big chunk of memory. This instructs the GC to
    garbage collect sooner than it would otherwise."""
    rgc.add_memory_pressure(estimate)

@unwrap_spec(w_frame=PyFrame)
def locals_to_fast(space, w_frame):
    assert isinstance(w_frame, PyFrame)
    w_frame.locals2fast()

@unwrap_spec(w_module=MixedModule)
def save_module_content_for_future_reload(space, w_module):
    w_module.save_module_content_for_future_reload()

def specialized_zip_2_lists(space, w_list1, w_list2):
    from pypy.objspace.std.specialisedtupleobject import specialized_zip_2_lists
    return specialized_zip_2_lists(space, w_list1, w_list2)

def set_code_callback(space, w_callable):
    cache = space.fromcache(CodeHookCache)
    if space.is_none(w_callable):
        cache._code_hook = None
    else:
        cache._code_hook = w_callable

@unwrap_spec(string='bytes', byteorder='text', signed=int)
def decode_long(space, string, byteorder='little', signed=1):
    from rpython.rlib.rbigint import rbigint, InvalidEndiannessError
    try:
        result = rbigint.frombytes(string, byteorder, bool(signed))
    except InvalidEndiannessError:
        raise oefmt(space.w_ValueError, "invalid byteorder argument")
    return space.newlong_from_rbigint(result)

def _promote(space, w_obj):
    """ Promote the first argument of the function and return it. Promote is by
    value for ints, floats, strs, unicodes (but not subclasses thereof) and by
    reference otherwise.  (Unicodes not supported right now.)

    This function is experimental!"""
    from rpython.rlib import jit
    if space.is_w(space.type(w_obj), space.w_int):
        jit.promote(space.int_w(w_obj))
    elif space.is_w(space.type(w_obj), space.w_float):
        jit.promote(space.float_w(w_obj))
    elif space.is_w(space.type(w_obj), space.w_bytes):
        jit.promote_string(space.bytes_w(w_obj))
    elif space.is_w(space.type(w_obj), space.w_unicode):
        raise oefmt(space.w_TypeError, "promoting unicode unsupported")
    else:
        jit.promote(w_obj)
    return w_obj

def stack_almost_full(space):
    """Return True if the stack is more than 15/16th full."""
    return space.newbool(rstack.stack_almost_full())

def side_effects_ok(space):
    """For use with the reverse-debugger: this function normally returns
    True, but will return False if we are evaluating a debugging command
    like a watchpoint.  You are responsible for not doing any side effect
    at all (including no caching) when evaluating watchpoints.  This
    function is meant to help a bit---you can write:

        if not __pypy__.side_effects_ok():
            skip the caching logic

    inside getter methods or properties, to make them usable from
    watchpoints.  Note that you need to re-run ``REVDB=.. pypy''
    after changing the Python code.
    """
    return space.newbool(space._side_effects_ok())

def revdb_stop(space):
    from pypy.interpreter.reverse_debugging import stop_point
    stop_point()

def pyos_inputhook(space):
    """Call PyOS_InputHook() from the CPython C API."""
    if not space.config.objspace.usemodules.cpyext:
        return
    w_modules = space.sys.get('modules')
    if space.finditem_str(w_modules, 'cpyext') is None:
        return      # cpyext not imported yet, ignore
    from pypy.module.cpyext.api import invoke_pyos_inputhook
    invoke_pyos_inputhook(space)

def utf8content(space, w_u):
    """ Given a unicode string u, return it's internal byte representation.
    Useful for debugging only. """
    from pypy.objspace.std.unicodeobject import W_UnicodeObject
    if type(w_u) is not W_UnicodeObject:
        raise oefmt(space.w_TypeError, "expected unicode string, got %T", w_u)
    return space.newbytes(w_u._utf8)

