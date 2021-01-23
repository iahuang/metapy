import ast
from . import core, _util

class MPRuntimeError(Exception): pass

class Stackframe:
    def __init__(self):
        self._locals = {}
    
    def set_var(self, name, value):
        self._locals[name] = value
    
    def resolve_name(self, name):
        return self._locals.get(name, None)

class Interpreter:
    """ Main interpreter class for MetaPy """
    def __init__(self):
        self.globals = {}
        self.stack = []
    
        self.current_stackframe = None

        # this is just here to make "if __name__ == "__main__" " work properly
        self.set_global("__name__", core.convert_pyobj("__main__"))
    
    def _debug_dump(self):
        """ Print a dump listing all current global symbols """

        headers = ["name", "internal type", "address", "no. members", "native value?"]
        rows = []

        for symbol, value in self.globals.items():
            rows.append([
                symbol,
                type(value).__name__,
                hex(id(value)),
                len(value.members),
                getattr(value, "native_value", "N/A")
            ])
        
        tbl = _util.DebugTable(rows, headers)
        tbl.draw_borders = False
        tbl.cell_pad = 2
        tbl.print()
    
    def set_global(self, name, value):
        """ Register name to a MPObject instance in the global scope """
        self.globals[name] = value

    def set_in_current_scope(self, name, value):
        """ Register name to a MPObject instance in the current scope """
        if self.current_stackframe:
            self.current_stackframe.set_var(name, value)
        else:
            self.set_global(name, value)
    
    def resolve_name(self, name):
        """ Find out what a variable name refers to in the current execution context """
        if self.current_stackframe:
            if val := self.current_stackframe.resolve_name(name):
                return val 
        
        return self.globals.get(name, None)
    
    def invoke_call(self, value, args=[], kwargs={}):
        """ Attempt to call a given MPObject or MPNativeFunction """

        if isinstance(value, core.MPNativeFunction):
            ret = value.invoke(*args, **kwargs)
            return ret
        elif isinstance(value, core.MPObject):
            call_method = value.get_member("__call__")
            if call_method is None: self.raise_error("Object is not callable")
            self.invoke_call(call_method, args, kwargs)

        raise Exception("todo: implement")

    def multi_eval(self, nodes):
        """ Evaluate multiple ast.Nodes at once """
        return [self.eval_expression(node) for node in nodes]
    
    def eval_expression(self, node):
        """ Given an ast.Node object, return an MPObject instance """

        if isinstance(node, ast.Expr):
            return self.eval_expression(node.value)

        if isinstance(node, ast.Constant):
            return core.convert_pyobj(node.value)
        
        if isinstance(node, ast.BinOp):
            # Lookup table of ast operations and their respective methods
            op_method_name = {
                ast.Add: "__add__",
                ast.Sub: "__sub__",
                ast.Mult: "__mul__",
                ast.Div: "__div__",
            }.get(type(node.op))

            if op_method_name is None:
                self.raise_error("Unsupported operation type \"{}\"".format(type(node.op).__name__))
            
            left = self.eval_expression(node.left)
            right = self.eval_expression(node.right)
            method = left.get_member(op_method_name)

            return self.invoke_call(method, [right])

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                sub_func = core.MPInteger(0).get_member("__sub__")
                operand = self.eval_expression(node.operand)
                return self.invoke_call(sub_func, [operand])

            self.raise_error("Unsupported node type \"{}\"".format(type(node.op).__name__), node)

        if isinstance(node, ast.Call):
            call_target = self.eval_expression(node.func)
            call_args = self.multi_eval(node.args)

            return self.invoke_call(call_target, call_args)
        
        if isinstance(node, ast.Name):
            val = self.resolve_name(node.id)
            if not val:
                self.raise_error("Undefined symbol \"{}\"".format(node.id), node)
            return val
        self.raise_error("Unsupported node type \"{}\"".format(type(node).__name__), node)


    def raise_error(self, message, offending_node=None):
        """ Create an MPRuntimeError, optionally citing a specific ast.Node """
        if offending_node:
            msg = "at {}:{} - {}".format(
                offending_node.lineno,
                offending_node.col_offset,
                message
            )
            raise MPRuntimeError(msg) 
        raise MPRuntimeError(message)

    def execute_node(self, node):
        """ Evaluate and run the contents of the given ast.Node. Doesn't return anything """

        if isinstance(node, ast.Assign):
            targets = node.targets
            
            for target in targets:
                if not isinstance(target, ast.Name):
                    self.raise_error("Invalid lefthand operand to assignment", target)
                
                target_name = target.id

                self.set_in_current_scope(target_name, self.eval_expression(node.value))
        elif isinstance(node, ast.Expr):
            self.eval_expression(node)
        else:
            self.raise_error("Unsupported syntax node type \"{}\"".format(type(node).__name__), node)
        
    def run(self, source, debug=True):
        """ Run a complete Python module """
        for node in ast.parse(source).body:
            print(core.dump(node))
            self.execute_node(node) 