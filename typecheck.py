import inspect
import re
from types import CodeType, ModuleType


def extend_function(func, code, position='start'):
    if position.lower() not in {'start', 'end'}:
        raise ValueError('Position must be start or end')

    source = inspect.getsource(func)

    matches = re.search(r'def (\w+)\s*\(((\s|.)*?)\)\s*:', source)
    func_signature_start_index = matches.start()
    func_signature_end_index = matches.end()

    try:
        index_newline_before_def = source[:func_signature_start_index].rindex('\n')
    except ValueError:  # not found
        index_newline_before_def = func_signature_start_index
    indentation = (func_signature_start_index - index_newline_before_def) * '    '

    code_with_indent = ('\n' + indentation).join(code.split('\n'))
    complete_source = source[:func_signature_end_index] + '\n' + indentation + code_with_indent + source[func_signature_end_index:]

    print(complete_source)
    print("*"*40)

    m = ModuleType('m')
    exec(complete_source, m.__dict__)

    func.__code__ = getattr(m, f.__name__).__code__
    func(1, 2, 3)


if __name__ == '__main__':
    def f(
            a, b
            , c):
        print("in func")


    extend_function(f, 'print("this is added!")\nprint("also this")', position='end')
