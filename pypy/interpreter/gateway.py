"""

Gateway between app-level and interpreter-level:
* BuiltinCode (call interp-level code from app-level)
* Gateway     (a space-independent gateway to a Code object)
* app2interp  (embed an app-level function into an interp-level callable)
* interp2app  (publish an interp-level object to be visible from app-level)
* exportall   (mass-call interp2app on a whole dict of objects)
* importall   (mass-call app2interp on a whole dict of objects)

"""

import types, sys

from pypy.interpreter.error import OperationError 
from pypy.interpreter import eval, pycode
from pypy.interpreter.function import Function, Method
from pypy.interpreter.baseobjspace import Wrappable
from pypy.interpreter.argument import Arguments
from pypy.tool.cache import Cache 

class BuiltinCode(eval.Code):
    "The code object implementing a built-in (interpreter-level) hook."

    # When a BuiltinCode is stored in a Function object,
    # you get the functionality of CPython's built-in function type.

    def __init__(self, func, ismethod=None, spacearg=None):
        "NOT_RPYTHON"
        # 'implfunc' is the interpreter-level function.
        # Note that this uses a lot of (construction-time) introspection.
        eval.Code.__init__(self, func.__name__)
        self.func = func
        self.docstring = func.__doc__
        # signature-based hacks: renaming arguments from w_xyz to xyz.
        # Currently we enforce the following signature tricks:
        #  * the first arg must be either 'self' or 'space'
        #  * 'w_' prefixes for the rest
        #  * '_w' suffix for the optional '*' argument
        #  * alternatively a final '__args__' means an Arguments()
        # Not exactly a clean approach XXX.
        # First extract the signature from the (CPython-level) code object
        argnames, varargname, kwargname = pycode.cpython_code_signature(func.func_code)
        argnames = list(argnames)
        lookslikemethod = argnames[:1] == ['self']
        if ismethod is None:
            ismethod = lookslikemethod
        if spacearg is None:
            spacearg = not lookslikemethod
        self.ismethod = ismethod
        self.spacearg = spacearg
        if spacearg:
            del argnames[0]

        assert kwargname is None, (
            "built-in function %r should not take a ** argument" % func)

        self.generalargs = argnames[-1:] == ['__args__']
        self.starargs = varargname is not None
        assert not (self.generalargs and self.starargs), (
            "built-in function %r has both __args__ and a * argument" % func)
        if self.generalargs:
            del argnames[-1]
            varargname = "args"
            kwargname = "keywords"
        elif self.starargs:
            assert varargname.endswith('_w'), (
                "argument *%s of built-in function %r should end in '_w'" %
                (varargname, func))
            varargname = varargname[:-2]

        for i in range(ismethod, len(argnames)):
            a = argnames[i]
            assert a.startswith('w_'), (
                "argument %s of built-in function %r should "
                "start with 'w_'" % (a, func))
            argnames[i] = a[2:]

        self.sig = argnames, varargname, kwargname
        self.minargs = len(argnames)
        if self.starargs:
            self.maxargs = sys.maxint
        else:
            self.maxargs = self.minargs

    def create_frame(self, space, w_globals, closure=None):
        return BuiltinFrame(space, self, w_globals)

    def signature(self):
        return self.sig

    def getdocstring(self):
        return self.docstring


class BuiltinFrame(eval.Frame):
    "Frame emulation for BuiltinCode."
    # This is essentially just a delegation to the 'func' of the BuiltinCode.
    # Initialization of locals is already done by the time run() is called,
    # via the interface defined in eval.Frame.

    def setfastscope(self, scope_w):
        argarray = list(scope_w)
        if self.code.generalargs:
            w_kwds = argarray.pop()
            w_args = argarray.pop()
            argarray.append(Arguments.frompacked(self.space, w_args, w_kwds))
        elif self.code.starargs:
            w_args = argarray.pop()
            argarray += self.space.unpacktuple(w_args)
        if self.code.ismethod:
            argarray[0] = self.space.unwrap_builtin(argarray[0])
        self.argarray = argarray

    def getfastscope(self):
        raise OperationError(self.space.w_TypeError,
          self.space.wrap("cannot get fastscope of a BuiltinFrame"))

    def run(self):
        argarray = self.argarray
        if self.code.spacearg:
            w_result = self.code.func(self.space, *argarray)
        else:
            w_result = self.code.func(*argarray)
        if w_result is None:
            w_result = self.space.w_None
        return w_result


class Gateway(Wrappable):
    """General-purpose utility for the interpreter-level to create callables
    that transparently invoke code objects (and thus possibly interpreted
    app-level code)."""

    # This is similar to a Function object, but not bound to a particular
    # object space. During the call, the object space is either given
    # explicitly as the first argument (for plain function), or is read
    # from 'self.space' for methods.

        # after initialization the following attributes should be set
        #   name
        #   _staticglobals 
        #   _staticdefs
        #
        #  getcode is called lazily to get the code object to construct
        #  the space-bound function

    NOT_RPYTHON_ATTRIBUTES = ['_staticglobals', '_staticdefs']

    def getcode(self, space):
        # needs to be implemented by subclasses
        raise TypeError, "abstract"
        
    def __spacebind__(self, space):
        # to wrap a Gateway, we first make a real Function object out of it
        # and the result is a wrapped version of this Function.
        return self.get_function(space)

    def get_function(self, space):
        return space.loadfromcache(self, 
                                   Gateway.build_all_functions, 
                                   self.getcache(space))

    def build_all_functions(self, space):
        "NOT_RPYTHON"
        # the construction is supposed to be done only once in advance,
        # but must be done lazily when needed only, because
        #   1) it depends on the object space
        #   2) the w_globals must not be built before the underlying
        #      _staticglobals is completely initialized, because
        #      w_globals must be built only once for all the Gateway
        #      instances of _staticglobals
        if self._staticglobals is None:
            w_globals = None
        else:
            # is there another Gateway in _staticglobals for which we
            # already have a w_globals for this space ?
            cache = self.getcache(space) 
            for value in self._staticglobals.itervalues():
                if isinstance(value, Gateway):
                    if value in cache.content: 
                        # yes, we share its w_globals
                        fn = cache.content[value] 
                        w_globals = fn.w_func_globals
                        break
            else:
                # no, we build all Gateways in the _staticglobals now.
                w_globals = build_dict(self._staticglobals, space)
        return self._build_function(space, w_globals)

    def getcache(self, space):
        return space._gatewaycache 

    def _build_function(self, space, w_globals):
        "NOT_RPYTHON"
        cache = self.getcache(space) 
        try: 
            return cache.content[self] 
        except KeyError: 
            defs = self.getdefaults(space)  # needs to be implemented by subclass
            code = self.getcode(space)
            fn = Function(space, code, w_globals, defs, forcename = self.name)
            cache.content[self] = fn 
            return fn

    def get_method(self, obj):
        # to get the Gateway as a method out of an instance, we build a
        # Function and get it.
        # the object space is implicitely fetched out of the instance
        space = obj.space
        fn = self.get_function(space)
        w_obj = space.wrap(obj)
        return Method(space, space.wrap(fn),
                      w_obj, space.type(w_obj))


class app2interp(Gateway):
    """Build a Gateway that calls 'app' at app-level."""

    NOT_RPYTHON_ATTRIBUTES = ['_staticcode'] + Gateway.NOT_RPYTHON_ATTRIBUTES
    
    def __init__(self, app, app_name=None):
        "NOT_RPYTHON"
        Gateway.__init__(self)
        # app must be a function whose name starts with 'app_'.
        if not isinstance(app, types.FunctionType):
            raise TypeError, "function expected, got %r instead" % app
        if app_name is None:
            if not app.func_name.startswith('app_'):
                raise ValueError, ("function name must start with 'app_'; "
                                   "%r does not" % app.func_name)
            app_name = app.func_name[4:]
        self.name = app_name
        self._staticcode = app.func_code
        self._staticglobals = app.func_globals
        self._staticdefs = list(app.func_defaults or ())

    def getcode(self, space):
        "NOT_RPYTHON"
        code = pycode.PyCode(space)
        code._from_code(self._staticcode)
        return code

    def getdefaults(self, space):
        "NOT_RPYTHON"
        return [space.wrap(val) for val in self._staticdefs]

    def __call__(self, space, *args_w):
        # to call the Gateway as a non-method, 'space' must be explicitly
        # supplied. We build the Function object and call it.
        fn = self.get_function(space)
        return space.call_function(space.wrap(fn), *args_w)

    def __get__(self, obj, cls=None):
        "NOT_RPYTHON"
        if obj is None:
            return self
        else:
            space = obj.space
            w_method = space.wrap(self.get_method(obj))
            def helper_method_caller(*args_w):
                return space.call_function(w_method, *args_w)
            return helper_method_caller

class interp2app(Gateway):
    """Build a Gateway that calls 'f' at interp-level."""
    def __init__(self, f, app_name=None):
        "NOT_RPYTHON"
        Gateway.__init__(self)
        # f must be a function whose name does NOT starts with 'app_'
        if not isinstance(f, types.FunctionType):
            raise TypeError, "function expected, got %r instead" % f
        if app_name is None:
            if f.func_name.startswith('app_'):
                raise ValueError, ("function name %r suspiciously starts "
                                   "with 'app_'" % f.func_name)
            app_name = f.func_name
        self._code = BuiltinCode(f)
        self.name = app_name
        self._staticdefs = list(f.func_defaults or ())
        self._staticglobals = None

    def getcode(self, space):
        return self._code

    def getdefaults(self, space):
        "NOT_RPYTHON"
        return self._staticdefs

    def get_method(self, obj):
       assert self._code.ismethod, (
           'global built-in function %r used as method' %
           self._code.func)
       return Gateway.get_method(self, obj)


def exportall(d, temporary=False):
    """NOT_RPYTHON: Publish every function from a dict."""
    if temporary:
        i2a = interp2app_temp
    else:
        i2a = interp2app
    for name, obj in d.items():
        if isinstance(obj, types.FunctionType):
            # names starting in 'app_' are supposedly already app-level
            if name.startswith('app_'):
                continue
            # ignore tricky functions with another interp-level meaning
            if name in ('__init__', '__new__'):
                continue
            # ignore names in '_xyz'
            if name.startswith('_') and not name.endswith('_'):
                continue
            if 'app_'+name not in d:
                d['app_'+name] = i2a(obj, name)

def export_values(space, dic, w_namespace):
    "NOT_RPYTHON"
    for name, w_value in dic.items():
        if name.startswith('w_'):
            if name == 'w_dict':
                w_name = space.wrap('__dict__')
            elif name == 'w_name':
                w_name = space.wrap('__name__')
            else:
                w_name = space.wrap(name[2:])
            space.setitem(w_namespace, w_name, w_value)

def importall(d, temporary=False):
    """NOT_RPYTHON: Import all app_-level functions as Gateways into a dict."""
    if temporary:
        a2i = app2interp_temp
    else:
        a2i = app2interp
    for name, obj in d.items():
        if name.startswith('app_') and name[4:] not in d:
            if isinstance(obj, types.FunctionType):
                d[name[4:]] = a2i(obj, name[4:])

def build_dict(d, space):
    """NOT_RPYTHON:
    Search all Gateways and put them into a wrapped dictionary."""
    w_globals = space.newdict([])
    for value in d.itervalues():
        if isinstance(value, Gateway):
            fn = value._build_function(space, w_globals)
            w_name = space.wrap(value.name)
            w_object = space.wrap(fn)
            space.setitem(w_globals, w_name, w_object)
    if hasattr(space, 'w_sys'):  # give them 'sys' if it exists already
        space.setitem(w_globals, space.wrap('sys'), space.w_sys)
    return w_globals


# 
# the next gateways are to be used only for 
# temporary/initialization purposes 
class app2interp_temp(app2interp):
    "NOT_RPYTHON"
    def getcache(self, space): 
        return self.__dict__.setdefault(space, Cache())
        #                               ^^^^^
        #                          armin suggested this 
     
class interp2app_temp(interp2app): 
    "NOT_RPYTHON"
    def getcache(self, space): 
        return self.__dict__.setdefault(space, Cache())
