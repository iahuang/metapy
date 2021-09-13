from metapy.mperr import MPInternalError
from typing import Type
from .interpreter import Interpreter
from . import core

class _PyBuiltinWrapper:
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        retval = self.f(*[core.convert_mpobj(arg) for arg in args], **kwargs)
        return core.convert_pyobj(retval)

def wrap_python_builtin(f):
    return core.create_native_function(_PyBuiltinWrapper(f))

def _load_native(interpreter: Interpreter, f):
    interpreter.set_in_current_scope(f.__name__, wrap_python_builtin(f))

def mp_print(*objs, **kwargs):
    print(*[obj.call_method("__str__").native_value for obj in objs], **kwargs)

def mp_range(a: core.MPInteger=None, b: core.MPInteger=None, c: core.MPInteger=None):
    core._assert_type(a, core.MPInteger) # A is required
    if b:core._assert_type(b, core.MPInteger)
    if c:core._assert_type(c, core.MPInteger)
    
    if b is None:
        return core.convert_pyobj(list(range(a.native_value)))
    
    if c is None:
        return core.convert_pyobj(list(range(a.native_value, b.native_value)))

    return core.convert_pyobj(list(range(a.native_value, b.native_value, c.native_value)))

def load_to_interpreter(interpreter: Interpreter):
    py_wrap_direct = [
        abs,
        all,
        any,
        ascii,
        bin,
        bool,
        callable,
        chr,
        hex,
        id,
        input,
        int,
        isinstance,
        issubclass,
        iter,
        len,
        list,
        print,
        ord,
        pow,
        range,
        reversed,
        round,
        str,
        sum,
        tuple,
        zip
    ]

    py_unsupported = [
        breakpoint,
        bytes,
        bytearray,
        classmethod,
        compile,
        complex,
        delattr,
        globals,
        locals,
        map,
        max,
        memoryview,
        min,
        next,
        object,
        oct,
        open,
        property,
        repr,
        set,
        setattr,
        slice,
        sorted,
        staticmethod,
        super,
        type,
        vars,
        __import__
    ]

    for f in py_wrap_direct:
        interpreter.set_global(f.__name__, wrap_python_builtin(f))
    
    for f in py_unsupported:
        interpreter.set_global(f.__name__, core.MPUnsupportedFunction())
    
    interpreter.set_global("print", core.create_native_function(mp_print))
    interpreter.set_global("range", core.create_native_function(mp_range))