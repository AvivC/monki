import inspect
import re

from types import CodeType, ModuleType
import inspect

_FUNC_SIGNATURE_REGEX = r'def (\w+)\s*\(((\s|.)*?)\)\s*:'
_INDENT_STRING = '    '


def extend_function(func, start='', end='', indent=0):
    if not start and not end:
        raise ValueError('Must supply code for at least one of "start" or "end" arguments.')

    func_source = get_function_source(func)

    unindented_sig_regex = re.search(_FUNC_SIGNATURE_REGEX, func_source)

    # added code will always have an indentation level of 1 - immediately under the function
    start_indented = _INDENT_STRING + ('\n' + _INDENT_STRING).join(start.split('\n'))
    end_indented = _INDENT_STRING + ('\n' + _INDENT_STRING).join(end.split('\n'))

    func_signature = func_source[:unindented_sig_regex.end()]
    original_body = func_source[unindented_sig_regex.end():]

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


def get_function_source(func):
    func_source = inspect.getsource(func)
    func_source = _unindent_source(func_source)
    func_source = _strip_leading_decorators(func_source)
    return func_source


def _indent_lines(code, indent_level, indent_string):
    relative_indent_string = indent_level * indent_string
    return relative_indent_string + ('\n' + relative_indent_string).join(code.splitlines())


def _unindent_source(func_source):
    signature_regex = re.search(_FUNC_SIGNATURE_REGEX, func_source)
    sig_start_index = signature_regex.start()

    # TODO: all of this probably currently doesn't support async syntax and such
    try:
        newline_before_sig_index = func_source[:sig_start_index].rindex('\n')  # get the new-line closest to the signature on it's left
        white_before_sig_index = newline_before_sig_index + 1  # truncate the newline itself
    except ValueError:  # no newline character found - we assume we are in the beginning of the row
        white_before_sig_index = 0

    source_before_sig = func_source[white_before_sig_index:sig_start_index]
    # source_before_sig = func_source[:sig_start_index]

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


def _strip_leading_decorators(source_unindented):
    signature_regex = re.search(_FUNC_SIGNATURE_REGEX, source_unindented)
    sig_start_index = signature_regex.start()
    return source_unindented[sig_start_index:]


def typecheck(f):
    check_lines = []
    for arg_name, arg_type in f.__annotations__.items():
        check_lines.append('if not isinstance({arg_name}, {arg_type}): '
                           'raise TypeError("{arg_name} must be of type {arg_type}. Was of type: {{actual_type}}".format(actual_type=type({arg_name}))'
                           .format(arg_name=arg_name, arg_type=arg_type.__name__))
    checks = '\n'.join(check_lines)
    extend_function(f, start=checks)
    return f


if __name__ == '__main__':
    def f(a, b, c: int):
        print("in func")

    extend_function(f, start='for i in range(5):', end='print("finished looping")', indent=1)
    f(1, 2, 3)