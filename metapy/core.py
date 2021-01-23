import ast

class MPObject:
    def __init__(self):
        self.members = {
            "__str__": create_native_function(lambda _self: str(_self))
        }
        
    def set_member(self, name, value):
        self.members[name] = value
    
    def get_member(self, name):
        """ Retrieve value of a class member, None if it doesn't exist """
        return self.members.get(name, None)

class MPPrimitive(MPObject):
    def __init__(self, val):
        super().__init__()
        self.native_value = val

        self.set_member("__str__", create_native_function(lambda _self: str(_self.native_value)))
        
class MPInteger(MPPrimitive):
    def __init__(self, val):
        super().__init__(val)
        self.set_member("__add__", create_native_function(self._add))
        self.set_member("__sub__", create_native_function(self._sub))
        self.set_member("__mul__", create_native_function(self._mul))
        self.set_member("__div__", create_native_function(self._div))
    
    def _add(self, x):
        return convert_pyobj(self.native_value + x.native_value)
    def _sub(self, x):
        return convert_pyobj(self.native_value - x.native_value)
    def _mul(self, x):
        return convert_pyobj(self.native_value * x.native_value)
    def _div(self, x):
        return convert_pyobj(self.native_value / x.native_value)

class MPString(MPPrimitive):
    def __init__(self, val):
        super().__init__(val)

class MPNone(MPPrimitive):
    def __init__(self):
        super().__init__(None)

class MPList(MPObject):
    def __init__(self, data=[]):
        super().__init__()
        self.data = data

        self.set_member("append", create_native_function(self._append))
        self.set_member("__len__", create_native_function(self._len))

    def _append(self, obj):
        self.data.append(obj)
    
    def _len(self):
        return convert_pyobj(len(self.data))

class MPFunction(MPObject):
    def __init__(self, body):
        super().__init__()
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

def _unsupported(*args, **kwargs):
    raise Exception("Unsupported function")

class MPUnsupportedFunction(MPNativeFunction):
    def __init__(self):
        super().__init__(_unsupported)

def create_implemented_function(source):
    return MPFunction(body=parse_body(source))

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
    else:
        raise Exception("Unsupported object type", type(obj))

def convert_mpobj(obj):
    """ Converts an MetaPy object into a native Python object """

    if isinstance(obj, MPPrimitive):
        return obj.native_value
    elif isinstance(obj, MPNativeFunction):
        return obj._func
    else:
        raise Exception("Unsupported object type")

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