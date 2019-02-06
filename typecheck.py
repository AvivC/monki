import inspect
import re

from types import CodeType, ModuleType

_FUNC_SIGNATURE_REGEX = r'def (\w+)\s*\(((\s|.)*?)\)\s*:'
_INDENT_STRING = '    '


def extend_function(func, start='', end='', indent=0):
    if not start and not end:
        raise ValueError('Must supply code for at least one of "start" or "end" arguments.')

    func_source = inspect.getsource(func)
    source_unindented = _unindent_source(func_source)

    unindented_sig_regex = re.search(_FUNC_SIGNATURE_REGEX, source_unindented)

    # added code will always have an indentation level of 1 - immediately under the function
    start_indented = _INDENT_STRING + ('\n' + _INDENT_STRING).join(start.split('\n'))
    end_indented = _INDENT_STRING + ('\n' + _INDENT_STRING).join(end.split('\n'))

    func_signature = source_unindented[:unindented_sig_regex.end()]
    original_body = source_unindented[unindented_sig_regex.end():]

    original_body_indented = _indent_lines(original_body, indent, _INDENT_STRING)

    modified_source = func_signature \
                      + '\n' \
                      + start_indented \
                      + original_body_indented \
                      + '\n' \
                      + end_indented

    print(modified_source)

    m = ModuleType('_internal_')
    exec(modified_source, m.__dict__)

    func.__code__ = getattr(m, f.__name__).__code__
    func(1, 2, 3)


def _indent_lines(code, indent_level, indent_string):
    relative_indent_string = indent_level * indent_string
    return relative_indent_string + ('\n' + relative_indent_string).join(code.splitlines())


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

    extend_function(f, start='try:', end="except: pass", indent=1)
