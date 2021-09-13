from __future__ import print_function
import ast
from typing import List
from . import core, _util, mperr
import sys

class Stackframe:
    def __init__(self, function_name):
        self._locals = {}
        self.function_name = function_name
    
    def set_var(self, name, value):
        self._locals[name] = value
    
    def resolve_name(self, name):
        return self._locals.get(name, None)

class Interpreter:
    """ Main interpreter class for MetaPy """
    def __init__(self):
        self.globals = {}
        self.stack: List[Stackframe] = []
        self.current_node = None

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
    
    @property
    def current_stackframe(self):
        if self.stack:
            return self.stack[-1]
        return None

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
        elif isinstance(value, core.MPFunction):
            self.stack.append(Stackframe(value.name))
            for node in value.body:
                self.current_node = node
                self.execute_node(node)
            self.stack.pop()
            
        elif isinstance(value, core.MPObject):
            call_method = value.get_member("__call__")
            if call_method is None: self.raise_error("Object is not callable")
            self.invoke_call(call_method, args, kwargs)
        else:
            raise Exception("todo: implement")

    def multi_eval(self, nodes):
        """ Evaluate multiple ast.Nodes at once """
        return [self.eval_expression(node) for node in nodes]
    
    def eval_expression(self, node):
        """ Given an ast.Node object, return an MPObject instance """

        self.current_node = node

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
            return left.call_method(op_method_name, [right])

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                zero = core.MPInteger(0)
                operand = self.eval_expression(node.operand)
                return zero.call_method("__sub__", [operand])

            self.raise_error("Unsupported node type \"{}\"".format(type(node.op).__name__))

        if isinstance(node, ast.Call):
            call_target = self.eval_expression(node.func)
            call_args = self.multi_eval(node.args)

            return self.invoke_call(call_target, call_args)
        
        if isinstance(node, ast.Name):
            val = self.resolve_name(node.id)
            if not val:
                self.raise_error("Undefined symbol \"{}\"".format(node.id))
            return val

        if isinstance(node, ast.List):
            elts = [self.eval_expression(el) for el in node.elts]
            
            return core.MPList(elts)
        self.raise_error("Unsupported syntax node type \"{}\"".format(type(node).__name__))


    def raise_error(self, message):
        """ Create an MPRuntimeError, optionally citing a specific ast.Node """
        offending_node = self.current_node

        raise mperr.MPRuntimeError(msg=message, node=offending_node)

    def execute_node(self, node):
        """ Evaluate and run the contents of the given ast.Node. Doesn't return anything """
        
        self.current_node = node

        if isinstance(node, ast.Assign):
            targets = node.targets
            
            for target in targets:
                if not isinstance(target, ast.Name):
                    self.raise_error("Invalid lefthand operand to assignment", target)
                
                target_name = target.id
                self.set_in_current_scope(target_name, self.eval_expression(node.value))
        elif isinstance(node, ast.Expr):
            self.eval_expression(node)
        elif isinstance(node, ast.FunctionDef):
            function_name = node.name
            args = node.args
            body = node.body

            function_object = core.MPFunction(name=function_name, body=body)

            self.set_in_current_scope(function_name, function_object)
        elif isinstance(node, ast.For):
            iter_over = self.eval_expression(node.iter)

            if hasattr(iter_over, "_arr_data"):
                data = iter_over._arr_data

                for _i in data:
                    self.set_in_current_scope(node.target.id, _i)
                    for body_node in node.body:
                        self.execute_node(body_node)
            else:
                self.raise_error("Cannot iterate over object of type "+str(type(iter_over).__name__))
        else:
            self.raise_error("Unsupported syntax node type \"{}\"".format(type(node).__name__), node)
    
    def print_err_stacktrace(self, err: mperr.MPRuntimeError):
        print("Traceback (most recent call last):", file=sys.stderr)
        print("  in <module>:", file=sys.stderr)
        for frame in self.stack:
            print("  in function " + frame.function_name+":", file=sys.stderr)

        where = "at {}:{} - ".format(
            err.node.lineno,
            err.node.col_offset,
        )
        print(where + err.msg, file=sys.stderr)

    def run(self, source, debug=False):
        """ Run a complete Python module """
        
        try:
            for node in ast.parse(source).body:
                self.current_node = node
                if debug: print(core.dump(node))
                self.execute_node(node) 
        except mperr.MPRuntimeError as err:
            self.print_err_stacktrace(err)
        except mperr.MPInternalError as err:
            self.print_err_stacktrace(mperr.MPRuntimeError(str(err), self.current_node))