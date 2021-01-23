from metapy import interpreter, builtins

intp = interpreter.Interpreter()
builtins.load_to_interpreter(intp)

intp._debug_dump()
print("running...")
intp.run("""
print("hello world!", 1)
print(abs(-11 + 2))
a = 1

""")
intp._debug_dump()