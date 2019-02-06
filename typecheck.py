import inspect
import re
from types import CodeType, ModuleType


_FUNC_SIGNATURE_REGEX = r'def (\w+)\s*\(((\s|.)*?)\)\s*:'
_INDENT_STRING = '    '


def extend_function(func, added_code, position='start'):
    if position.lower() not in {'start', 'end'}:
        raise ValueError('Position must be \'start\' or \'end\'')

    func_source = inspect.getsource(func)
    source_unindented = _unindent_source(func_source)

    unindented_sig_regex = re.search(_FUNC_SIGNATURE_REGEX, source_unindented)

    # added code will always have an indentation level of 1 - immediately under the function
    added_code_indented = _INDENT_STRING + ('\n' + _INDENT_STRING).join(added_code.split('\n'))

    func_signature = source_unindented[:unindented_sig_regex.end()]
    original_body = source_unindented[unindented_sig_regex.end():]

    modified_source = func_signature \
                      + '\n' \
                      + added_code_indented \
                      + original_body

    print(modified_source)

    m = ModuleType('_internal_')
    exec(modified_source, m.__dict__)

    func.__code__ = getattr(m, f.__name__).__code__
    func(1, 2, 3)


def _unindent_source(func_source):
    signature_regex = re.search(_FUNC_SIGNATURE_REGEX, func_source)
    func_sig_start_index = signature_regex.start()

    source_before_sig = func_source[:func_sig_start_index]
    if not all(s == ' ' for s in source_before_sig):
        raise RuntimeError('All of the text before the function signature should be whitespace.')
    func_indent_level = int(len(source_before_sig) / len(_INDENT_STRING))  # int to indicate level of indentation
    after_indent_index = func_indent_level * len(_INDENT_STRING)
    source_unindented_lines = []
    for line in func_source.splitlines():
        unindented = line[after_indent_index:]
        source_unindented_lines.append(unindented)
    source_unindented = '\n'.join(source_unindented_lines)
    return source_unindented




if __name__ == '__main__':
    def f(a, b, c):
        print("in func")


    extend_function(f, 'print("this is added!")\nprint("also this")', position='end')
