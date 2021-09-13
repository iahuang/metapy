class MPRuntimeError(Exception):
    def __init__(self, msg, node):
        self.msg = msg
        self.node = node

class MPNameError(MPRuntimeError): pass
class MPSyntaxError(MPRuntimeError): pass
    
# To be thrown from functions outside the interpreter --
# will be caught during execution and displayed as a runtime error.
class MPInternalError(Exception): pass