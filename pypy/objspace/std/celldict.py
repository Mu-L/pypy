from pypy.objspace.std.dictmultiobject import IteratorImplementation
from pypy.objspace.std.dictmultiobject import W_DictMultiObject, _is_sane_hash
from pypy.rlib import jit

class ModuleCell(object):
    def __init__(self, w_value=None):
        self.w_value = w_value

    def invalidate(self):
        w_value = self.w_value
        self.w_value = None
        return w_value

    def __repr__(self):
        return "<ModuleCell: %s>" % (self.w_value, )

class ModuleDictImplementation(W_DictMultiObject):
    def __init__(self, space):
        self.space = space
        self.content = {}
        self.unshadowed_builtins = {}

    def getcell(self, key, make_new=True):
        res = self.content.get(key, None)
        if res is not None:
            return res
        if not make_new:
            return None
        result = self.content[key] = ModuleCell()
        return result

    def add_unshadowed_builtin(self, name, builtin_impl):
        assert isinstance(builtin_impl, ModuleDictImplementation)
        self.unshadowed_builtins[name] = builtin_impl

    def invalidate_unshadowed_builtin(self, name):
        impl = self.unshadowed_builtins[name]
        try:
            cell = impl.content[name]
        except KeyError:
            pass
        else:
            w_value = cell.invalidate()
            cell = impl.content[name] = ModuleCell(w_value)

    def impl_setitem(self, w_key, w_value):
        space = self.space
        if space.is_w(space.type(w_key), space.w_str):
            self.impl_setitem_str(w_key, w_value)
        else:
            self._as_rdict().setitem(w_key, w_value)

    def impl_setitem_str(self, w_key, w_value, shadows_type=True):
        name = self.space.str_w(w_key)
        self.getcell(name).w_value = w_value
        
        if name in self.unshadowed_builtins:
            self.invalidate_unshadowed_builtin(name)
            del self.unshadowed_builtins[name]

    def impl_delitem(self, w_key):
        space = self.space
        w_key_type = space.type(w_key)
        if space.is_w(w_key_type, space.w_str):
            key = space.str_w(w_key)
            cell = self.getcell(key, False)
            if cell is None:
                raise KeyError
            cell.invalidate()
            del self.content[key]
        elif _is_sane_hash(space, w_key_type):
            raise KeyError
        else:
            self._as_rdict().delitem(w_key)
        
    def impl_length(self):
        return len(self.content)

    def impl_getitem(self, w_lookup):
        space = self.space
        w_lookup_type = space.type(w_lookup)
        if space.is_w(w_lookup_type, space.w_str):
            res = self.getcell(space.str_w(w_lookup), False)
            if res is None:
                return None
            return res.w_value
        elif _is_sane_hash(space, w_lookup_type):
            return None
        else:
            return self._as_rdict().getitem(w_lookup)

    def impl_iter(self):
        return ModuleDictIteratorImplementation(self.space, self)

    def impl_keys(self):
        space = self.space
        return [space.wrap(key) for key in self.content.iterkeys()]

    def impl_values(self):
        return [cell.w_value for cell in self.content.itervalues()]

    def impl_items(self):
        space = self.space
        return [space.newtuple([space.wrap(key), cell.w_value])
                    for (key, cell) in self.content.iteritems()]

    def impl_clear(self):
        # inefficient, but who cares
        for k, cell in self.content.iteritems():
            cell.invalidate()
        for k in self.unshadowed_builtins:
            self.invalidate_unshadowed_builtin(k)
        self.content.clear()
        self.unshadowed_builtins.clear()


    def _as_rdict(self):
        r_dict_content = self.initialize_as_rdict()
        for k, cell in self.content.iteritems():
            r_dict_content[self.space.wrap(k)] = cell.w_value
            cell.invalidate()
        for k in self.unshadowed_builtins:
            self.invalidate_unshadowed_builtin(k)
        self.content = None
        self.unshadowed_builtins = None
        return self

class ModuleDictIteratorImplementation(IteratorImplementation):
    def __init__(self, space, dictimplementation):
        IteratorImplementation.__init__(self, space, dictimplementation)
        self.iterator = dictimplementation.content.iteritems()

    def next_entry(self):
        # note that this 'for' loop only runs once, at most
        for key, cell in self.iterator:
            return (self.space.wrap(key), cell.w_value)
        else:
            return None, None


class State(object):
    def __init__(self, space):
        self.space = space
        self.invalidcell = ModuleCell()
        self.always_invalid_cache = []
        self.neverused_dictimpl = ModuleDictImplementation(space)

class GlobalCacheHolder(object):
    def __init__(self, space):
        self.cache = None
        state = space.fromcache(State)
        self.dictimpl = state.neverused_dictimpl

    def getcache(self, space, code, w_globals):
        implementation = getimplementation(w_globals)
        if self.dictimpl is implementation:
            return self.cache
        return self.getcache_slow(space, code, w_globals, implementation)
    getcache._always_inline_ = True

    def getcache_slow(self, space, code, w_globals, implementation):
        state = space.fromcache(State)
        if not isinstance(implementation, ModuleDictImplementation):
            cache = state.always_invalid_cache
            if len(code.co_names_w) > len(cache):
                cache = [state.invalidcell] * len(code.co_names_w)
                state.always_invalid_cache = cache
        else:
            cache = [state.invalidcell] * len(code.co_names_w)
        self.cache = cache
        self.dictimpl = implementation
        return cache
    getcache_slow._dont_inline_ = True

def init_code(code):
    code.globalcacheholder = GlobalCacheHolder(code.space)


def get_global_cache(space, code, w_globals):
    from pypy.interpreter.pycode import PyCode
    assert isinstance(code, PyCode)
    holder = code.globalcacheholder
    return holder.getcache(space, code, w_globals)

def getimplementation(w_dict):
    if type(w_dict) is ModuleDictImplementation and w_dict.r_dict_content is None:
        return w_dict
    else:
        return None

def LOAD_GLOBAL(f, nameindex, *ignored):
    cell = f.cache_for_globals[nameindex]
    w_value = cell.w_value
    if w_value is None:
        # slow path
        w_value = load_global_fill_cache(f, nameindex)
    f.pushvalue(w_value)
LOAD_GLOBAL._always_inline_ = True

def find_cell_from_dict(implementation, name):
    if isinstance(implementation, ModuleDictImplementation):
        return implementation.getcell(name, False)
    return None

@jit.dont_look_inside
def load_global_fill_cache(f, nameindex):
    name = f.space.str_w(f.getname_w(nameindex))
    implementation = getimplementation(f.w_globals)
    if isinstance(implementation, ModuleDictImplementation):
        cell = find_cell_from_dict(implementation, name)
        if cell is None:
            builtin_impl = getimplementation(f.get_builtin().getdict())
            cell = find_cell_from_dict(builtin_impl, name)
            if cell is not None:
                implementation.add_unshadowed_builtin(name, builtin_impl)
            
        if cell is not None:
            f.cache_for_globals[nameindex] = cell
            return cell.w_value
    return f._load_global(f.getname_w(nameindex))
load_global_fill_cache._dont_inline_ = True
