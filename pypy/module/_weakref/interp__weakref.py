import py
from pypy.interpreter.baseobjspace import Wrappable, W_Root
from pypy.interpreter.argument import Arguments
from pypy.interpreter.error import OperationError
from pypy.interpreter.typedef import GetSetProperty, TypeDef
from pypy.interpreter.gateway import interp2app, ObjSpace
import weakref


class WeakrefLifeline(object):
    def __init__(self):
        self.refs_weak = []
        self.cached_weakref_index = -1
        self.cached_proxy_index = -1
        
    def __del__(self):
        for i in range(len(self.refs_weak) - 1, -1, -1):
            w_ref = self.refs_weak[i]()
            if w_ref is not None:
                w_ref.activate_callback()
    
    def get_or_make_weakref(self, space, w_subtype, w_obj, w_callable):
        w_weakreftype = space.gettypeobject(W_Weakref.typedef)
        is_weakreftype = space.is_w(w_weakreftype, w_subtype)
        can_reuse = space.is_w(w_callable, space.w_None)
        if is_weakreftype and can_reuse and self.cached_weakref_index >= 0:
            w_cached = self.refs_weak[self.cached_weakref_index]()
            if w_cached is not None:
                return w_cached
            else:
                self.cached_weakref_index = -1
        w_ref = space.allocate_instance(W_Weakref, w_subtype)
        index = len(self.refs_weak)
        W_Weakref.__init__(w_ref, space, w_obj, w_callable)
        self.refs_weak.append(weakref.ref(w_ref))
        if is_weakreftype and can_reuse:
            self.cached_weakref_index = index
        return w_ref

    def get_or_make_proxy(self, space, w_obj, w_callable):
        can_reuse = space.is_w(w_callable, space.w_None)
        if can_reuse and self.cached_proxy_index >= 0:
            w_cached = self.refs_weak[self.cached_proxy_index]()
            if w_cached is not None:
                return w_cached
            else:
                self.cached_proxy_index = -1
        index = len(self.refs_weak)
        if space.is_true(space.callable(w_obj)):
            w_proxy = W_CallableProxy(space, w_obj, w_callable)
        else:
            w_proxy = W_Proxy(space, w_obj, w_callable)
        self.refs_weak.append(weakref.ref(w_proxy))
        if can_reuse:
            self.cached_proxy_index = index
        return w_proxy

    def get_any_weakref(self, space):
        if self.cached_weakref_index != -1:
            w_ref = self.refs_weak[self.cached_weakref_index]()
            if w_ref is not None:
                return w_ref
        w_weakreftype = space.gettypeobject(W_Weakref.typedef)
        for i in range(len(self.refs_weak)):
            w_ref = self.refs_weak[i]()
            if (w_ref is not None and 
                space.is_true(space.isinstance(w_ref, w_weakreftype))):
                return w_ref
        return space.w_None

class W_WeakrefBase(Wrappable):
    def __init__(w_self, space, w_obj, w_callable):
        w_self.space = space
        w_self.w_obj_weak = weakref.ref(w_obj)
        w_self.w_callable = w_callable

    def dereference(self):
        w_obj = self.w_obj_weak()
        if w_obj is None:
            return self.space.w_None
        return w_obj
        
    def activate_callback(w_self):
        if not w_self.space.is_w(w_self.w_callable, w_self.space.w_None):
            try:
                w_self.space.call_function(w_self.w_callable, w_self)
            except OperationError, e:
                e.write_unraisable(w_self.space, 'function', w_self.w_callable)


class W_Weakref(W_WeakrefBase):
    def __init__(w_self, space, w_obj, w_callable):
        W_WeakrefBase.__init__(w_self, space, w_obj, w_callable)
        w_self.w_hash = None

    def descr_hash(self):
        if self.w_hash is not None:
            return self.w_hash
        w_obj = self.dereference()
        if self.space.is_w(w_obj, self.space.w_None):
            raise OperationError(self.space.w_TypeError,
                                 self.space.wrap("weak object has gone away"))
        self.w_hash = self.space.hash(w_obj)
        return self.w_hash

def descr__new__weakref(space, w_subtype, w_obj, w_callable=None):
    lifeline = w_obj.getweakref()
    if lifeline is None:
        lifeline = WeakrefLifeline()
        w_obj.setweakref(space, lifeline)
    return lifeline.get_or_make_weakref(space, w_subtype, w_obj, w_callable)

def descr__eq__(space, ref1, ref2):
    w_obj1 = ref1.dereference()
    w_obj2 = ref2.dereference()
    if (space.is_w(w_obj1, space.w_None) or
        space.is_w(w_obj2, space.w_None)):
        return space.is_(ref1, ref2)
    return space.eq(w_obj1, w_obj2)

def descr__ne__(space, ref1, ref2):
    return space.not_(space.eq(ref1, ref2))

W_Weakref.typedef = TypeDef("weakref",
    __doc__ = """A weak reference to an object 'obj'.  A 'callback' can given,
which is called with the weak reference as an argument when 'obj'
is about to be finalized.""",
    __new__ = interp2app(descr__new__weakref),
    __eq__ = interp2app(descr__eq__,
                        unwrap_spec=[ObjSpace, W_Weakref, W_Weakref]),
    __ne__ = interp2app(descr__ne__,
                        unwrap_spec=[ObjSpace, W_Weakref, W_Weakref]),
    __hash__ = interp2app(W_Weakref.descr_hash, unwrap_spec=['self']),
    __call__ = interp2app(W_Weakref.dereference, unwrap_spec=['self'])
)


def getweakrefcount(space, w_obj):
    """Return the number of weak references to 'obj'."""
    lifeline = w_obj.getweakref()
    if lifeline is None:
        return space.wrap(0)
    else:
        result = 0
        for i in range(len(lifeline.refs_weak)):
            if lifeline.refs_weak[i]() is not None:
                result += 1
        return space.wrap(result)

def getweakrefs(space, w_obj):
    """Return a list of all weak reference objects that point to 'obj'."""
    lifeline = w_obj.getweakref()
    if lifeline is None:
        return space.newlist([])
    else:
        result = []
        for i in range(len(lifeline.refs_weak)):
            w_ref = lifeline.refs_weak[i]()
            if w_ref is not None:
                result.append(w_ref)
        return space.newlist(result)

#_________________________________________________________________
# Proxy

class W_Proxy(W_WeakrefBase):
    def descr__hash__(self, space):
        raise OperationError(space.w_TypeError,
                             space.wrap("unhashable type"))

class W_CallableProxy(W_Proxy):
    def descr__call__(self, space, __args__):
        w_obj = force(space, self)
        return space.call_args(w_obj, __args__)

def proxy(space, w_obj, w_callable=None):
    """Create a proxy object that weakly references 'obj'.
'callback', if given, is called with the proxy as an argument when 'obj'
is about to be finalized."""
    lifeline = w_obj.getweakref()
    if lifeline is None:
        lifeline = WeakrefLifeline()
        w_obj.setweakref(space, lifeline) 
    return lifeline.get_or_make_proxy(space, w_obj, w_callable)

def descr__new__proxy(space, w_subtype, w_obj, w_callable=None):
    raise OperationError(
        space.w_TypeError,
        space.wrap("cannot create 'weakproxy' instances"))

def descr__new__callableproxy(space, w_subtype, w_obj, w_callable=None):
    raise OperationError(
        space.w_TypeError,
        space.wrap("cannot create 'weakcallableproxy' instances"))


def force(space, proxy):
    if not isinstance(proxy, W_Proxy):
        return proxy
    w_obj = proxy.dereference()
    assert w_obj is not None
    if space.is_w(w_obj, space.w_None):
        raise OperationError(
            space.w_ReferenceError,
            space.wrap("weakly referenced object no longer exists"))
    return w_obj

proxy_typedef_dict = {}
callable_proxy_typedef_dict = {}
special_ops = {'repr': True, 'userdel': True, 'hash': True}

for opname, _, arity, special_methods in ObjSpace.MethodTable:
    if opname in special_ops:
        continue
    nonspaceargs =  ", ".join(["w_obj%s" % i for i in range(arity)])
    code = "def func(space, %s):\n    '''%s'''\n" % (nonspaceargs, opname)
    for i in range(arity):
        code += "    w_obj%s = force(space, w_obj%s)\n" % (i, i)
    code += "    return space.%s(%s)" % (opname, nonspaceargs)
    exec py.code.Source(code).compile()
    for special_method in special_methods:
        proxy_typedef_dict[special_method] = interp2app(
            func, unwrap_spec=[ObjSpace] + [W_Root] * arity)
        callable_proxy_typedef_dict[special_method] = interp2app(
            func, unwrap_spec=[ObjSpace] + [W_Root] * arity)


W_Proxy.typedef = TypeDef("weakproxy",
    __new__ = interp2app(descr__new__proxy),
    __hash__ = interp2app(W_Proxy.descr__hash__, unwrap_spec=['self', ObjSpace]),
    **proxy_typedef_dict)
W_Proxy.typedef.acceptable_as_base_class = False

W_CallableProxy.typedef = TypeDef("weakcallableproxy",
    __new__ = interp2app(descr__new__callableproxy),
    __hash__ = interp2app(W_Proxy.descr__hash__, unwrap_spec=['self', ObjSpace]),
    __call__ = interp2app(W_CallableProxy.descr__call__,
                          unwrap_spec=['self', ObjSpace, Arguments]), 
    **callable_proxy_typedef_dict)
W_CallableProxy.typedef.acceptable_as_base_class = False
