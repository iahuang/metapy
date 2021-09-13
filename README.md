# MetaPy
*A sandboxed Python interpreter, written in Python.*

## About

Metapy is designed to be a sandboxed Python execution environment, useful for running untrusted or potentially unsafe code.

Metapy implements a subset of the Python language and does not provide implementations for most of the Python Standard library, although library implementations can be provided for the execution environment as needed.

## Basic Usage

```python
from metapy import interpreter, builtins

# Create a new Interpreter object
intp = interpreter.Interpreter()

# Load built-in functions like print, range, etc.
# This step is technically optional
builtins.load_to_interpreter(intp)

# Run a snippet of Python code
program = """
print("Hello world!")
"""

try:
    intp.run(program)
except interpreter.MPRuntimeError as e:
    print("an error occurred while running this program:", str(e))
```
## Limitations

### Built-in functions

Not all built-in functions are supported at the moment. For some functions such as `open()`, this is an intentional security feature. To see a list of currently supported built-ins, use `metapy.Interpreter()._dump_debug()`

### Typing

MetaPy's internal typing system functions differently than in CPython, code that relies heavily on meta type-checking may work diferently.