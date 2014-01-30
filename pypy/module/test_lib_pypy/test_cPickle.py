from __future__ import absolute_import
import pypy._py as py

from lib_pypy import cPickle

def test_stack_underflow():
    py.test.raises(cPickle.UnpicklingError, cPickle.loads, "a string")
