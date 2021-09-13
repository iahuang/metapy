from metapy import interpreter, builtins

intp = interpreter.Interpreter()
builtins.load_to_interpreter(intp)

intp.run("""
print("hello world!", 1)
print(abs(-11 + 2))

a = [1, 2, 3, "yes", "no"]

def ffn():
    for a in [1, 2, 3, 4] + [1, 2] + a:
        print(a)

ffn()
print(type)
""")


#intp._debug_dump()