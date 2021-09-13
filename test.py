from metapy import interpreter, builtins

intp = interpreter.Interpreter()
builtins.load_to_interpreter(intp)

intp.run("""
print("hello world!", 1)
print(abs(-11 + 2))

a = [1, 2, 3, "yes", "no"]

def n():
    a = 1
    print(a)
    fads
    print("deon sucks")

n()
""")

#intp._debug_dump()