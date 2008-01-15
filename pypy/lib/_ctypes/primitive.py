import _rawffi

SIMPLE_TYPE_CHARS = "cbBhHiIlLdfuzZqQPXOv"

from _ctypes.basics import _CData, _CDataMeta, cdata_from_address

class NULL(object):
    pass
NULL = NULL()

TP_TO_DEFAULT = {
        'c': 0,
        'b': 0,
        'B': 0,
        'h': 0,
        'H': 0,
        'i': 0,
        'I': 0,
        'l': 0,
        'L': 0,
        'q': 0,
        'Q': 0,
        'f': 0.0,
        'd': 0.0,
        'P': None,
        # not part of struct
        'O': NULL,
        'z': None,
}
 
DEFAULT_VALUE = object()

class SimpleType(_CDataMeta):
    def __new__(self, name, bases, dct):
        tp = dct['_type_']
        if (not isinstance(tp, str) or
            not len(tp) == 1 or
            tp not in SIMPLE_TYPE_CHARS):
            raise ValueError('%s is not a type character' % (tp))
        default = TP_TO_DEFAULT[tp]
        ffiarray = _rawffi.Array(tp)
        result = type.__new__(self, name, bases, dct)
        result._ffiletter = tp
        result._ffiarray = ffiarray
        if tp == 'z':
            # c_char_p special cases
            from _ctypes import Array, _Pointer

            def _getvalue(self):
                return _rawffi.charp2string(self._buffer[0])
            def _setvalue(self, value):
                if isinstance(value, str):
                    array = _rawffi.Array('c')(len(value)+1, value)
                    value = array.buffer
                    # XXX free 'array' later
                self._buffer[0] = value
            result.value = property(_getvalue, _setvalue)

            def from_param(self, value):
                if value is None:
                    return None
                if isinstance(value, basestring):
                    return self(value)
                if isinstance(value, self):
                    return value
                if isinstance(value, (Array, _Pointer)):
                    if type(value)._type_ == 'c':
                        return value
                return _SimpleCData.from_param(self, value)
            result.from_param = classmethod(from_param)

        return result

    from_address = cdata_from_address

    def from_param(self, value):
        if isinstance(value, self):
            return value
        try:
            return self(value)
        except (TypeError, ValueError):
            return super(SimpleType, self).from_param(value)

    def _sizeofinstances(self):
        return _rawffi.sizeof(self._type_)

class _SimpleCData(_CData):
    __metaclass__ = SimpleType
    _type_ = 'i'

    def __init__(self, value=DEFAULT_VALUE):
        self._buffer = self._ffiarray(1)
        if value is not DEFAULT_VALUE:
            self.value = value

    def _getvalue(self):
        return self._buffer[0]

    def _setvalue(self, value):
        self._buffer[0] = value
    value = property(_getvalue, _setvalue)
    del _getvalue, _setvalue

    def __ctypes_from_outparam__(self):
        return self.value

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.value)
