import ast
from typing import Type
from . import mperr

class MPObject:
    def __init__(self):
        self.members = {
            "__str__": create_native_function(MPObject._str)
        }
    
    @staticmethod
    def _str(_self):
        return MPString(str(_self))
        
    def set_member(self, name, value):
        self.members[name] = value
    
    def get_member(self, name):
        """ Retrieve value of a class member """
        
        if not name in self.members:
            raise mperr.MPInternalError(f'Object has no attribute or method "{name}"')
        
        return self.members[name]
    
    def call_method(self, name, args=[], kwargs={}):
        method = self.get_member(name)
        return method.invoke(*([self]+args), **kwargs)


class MPPrimitive(MPObject):
    def __init__(self, val):
        super().__init__()
        self.native_value = val

        self.set_member("__str__", create_native_function(MPPrimitive._str))
    
    @staticmethod
    def _str(_self):
        return MPString(_self.native_value)

class MPInteger(MPPrimitive):
    def __init__(self, val):
        super().__init__(val)
        self.set_member("__add__", create_native_function(MPInteger._add))
        self.set_member("__sub__", create_native_function(MPInteger._sub))
        self.set_member("__mul__", create_native_function(MPInteger._mul))
        self.set_member("__div__", create_native_function(MPInteger._div))
    
    @staticmethod
    def _add(_self, x):
        return convert_pyobj(_self.native_value + x.native_value)
    @staticmethod
    def _sub(_self, x):
        return convert_pyobj(_self.native_value - x.native_value)
    @staticmethod
    def _mul(_self, x):
        return convert_pyobj(_self.native_value * x.native_value)
    @staticmethod
    def _div(_self, x):
        return convert_pyobj(_self.native_value / x.native_value)

class MPString(MPPrimitive):
    def __init__(self, val):
        super().__init__(val)

class MPNone(MPPrimitive):
    def __init__(self):
        super().__init__(None)

class MPList(MPObject):
    def __init__(self, data=[]):
        super().__init__()
        self._arr_data = data

        self.set_member("append", create_native_function(self._append))
        self.set_member("copy", create_native_function(self._copy))
        self.set_member("__len__", create_native_function(self._len))
        self.set_member("__str__", create_native_function(MPList._str))
        self.set_member("__add__", create_native_function(self._add))

    @staticmethod
    def _str(_self):
        s = str([el.call_method("__str__").native_value for el in _self._arr_data])
        return MPString(s)
    
    def _add(self, a, b):
        _assert_type(a, MPList)
        _assert_type(b, MPList)
        return MPList(a._arr_data+b._arr_data)

    def _append(self, obj):
        self._arr_data.append(obj)
    
    def _len(self):
        return convert_pyobj(len(self._arr_data))
    
    def _copy(self):
        return convert_pyobj(self._arr_data[:])

class MPFunction(MPObject):
    def __init__(self, name, body):
        super().__init__()
        self.name = name
        self.body = body

class MPNativeFunction:
    """
    MPNativeFunction does not derive from the base MPObject class.
    The reason for this is that the base MPObject has class members
    that derive from MPNativeFunction, therefore creating a circular
    dependency.

    In most regards, MPNativeFunction behaves like a MPObject class,
    but is not technically an MPObject.
    """
    def __init__(self, func):
        self._func = func
        self.members = {}
    
    def invoke(self, *args, **kwargs):
        retval = self._func(*args, **kwargs)

        # implicitly return None
        if retval is None:
            return MPNone()
        
        return retval
    
    def call_method(self, name, args=[], kwargs={}):
        if name == "__str__":
            return convert_pyobj("<UnsupportedFunction>")

def _unsupported(*args, **kwargs):
    raise mperr.MPInternalError("Unsupported function call")

class MPUnsupportedFunction(MPNativeFunction):
    def __init__(self):
        super().__init__(_unsupported)

# def create_implemented_function(source):
#     return MPFunction(name="", body=parse_body(source))

""" Conversion + creation functions """

def create_native_function(func):
    return MPNativeFunction(func)

def convert_pyobj(obj):
    """ Converts a Python object into a MPObject instance """

    if isinstance(obj, int):
        return MPInteger(obj)
    elif isinstance(obj, str):
        return MPString(obj)
    elif obj is None:
        return MPNone()
    elif isinstance(obj, list):
        return MPList(data=[convert_pyobj(item) for item in obj])
    else:
        raise mperr.MPInternalError("Unsupported object type", type(obj))

def convert_mpobj(obj):
    """ Converts an MetaPy object into a native Python object """

    if isinstance(obj, MPPrimitive):
        return obj.native_value
    elif isinstance(obj, MPNativeFunction):
        return obj._func
    else:
        raise mperr.MPInternalError("Unsupported object type")

# internally code bodies are represented using native AST objects
def parse_body(source):
    return ast.parse(source).body

def dump(node):
    return ast.dump(node)

def dump_body(body):
    dumps = [dump(node) for node in body]
    output = "[\n"
    for d in dumps:
        output+="    "+d+",\n"
    output+="]"
    return output

""" Assertion functions """

def _assert_type(obj: MPObject, type: Type):
    if not isinstance(obj, type):
        raise mperr.MPInternalError(f'Expected type {type}, found object of type {_typeof(obj)}')

def _typeof(obj: MPObject):
    return type(obj).__name__

def _assert_iterable(obj: MPObject):
    if not hasattr(obj, "_arr_data"):
        raise mperr.MPInternalError(f'Object of type {_typeof(obj)} is not iterable!')