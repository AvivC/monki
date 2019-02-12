import itertools
import re
import types

from types import CodeType, ModuleType
import inspect


_FUNC_SIGNATURE_REGEX = r'def (\w+)\s*\(((\s|.)*?)\)\s*:'
_INDENT_STRING = '    '


def extend_function(func, start='', end='', indent_inner=False):
    if indent_inner is True:
        indent_inner = 1
    elif indent_inner is False:
        indent_inner = 0

    modified_source = _modify_source(func, start, end, indent_inner)
    _replace_code(func, modified_source)


def _replace_code(func, modified_source):
    modified_function = _create_modified_function(func, modified_source)
    modified_code_object = modified_function.__code__
    try:
        func.__code__ = modified_code_object
    except ValueError as e:
        if 'requires a code object with' in str(e).lower():  # making sure it's the right exception
            raise ValueError('Setting variables from outer function in extension - currently not supported.') from e
        else:
            raise


def _create_modified_function(func, modified_source):
    throwaway_module = ModuleType('_internal_')

    is_closure = func.__closure__ is not None
    if is_closure:
        modified_function = _modify_closure_function(func, modified_source, throwaway_module)

    else:
        _create_function_in_inner_module(modified_source, throwaway_module)
        modified_function = getattr(throwaway_module, func.__name__)

    return modified_function


def _modify_closure_function(func, modified_source, throwaway_module):
    func_freevars = func.__code__.co_freevars
    freevars_declarations = '\n    '.join('{} = None'.format(varname) for varname in func_freevars)

    closure_signature, closure_body = _divide_source(modified_source)
    closure_body = _indent_lines(closure_body, indent_level=1, indent_string=_INDENT_STRING)
    closure_source = closure_signature + closure_body

    wrapper_name = '_wrapper'
    wrapper_source = \
        """def {wrapper_name}():\n    {freevars_declarations}\n    {closure_source}\n    return {func_name}""".format(
            freevars_declarations=freevars_declarations,
            closure_source=closure_source,
            func_name=func.__name__,
            wrapper_name=wrapper_name)

    _create_function_in_inner_module(wrapper_source, throwaway_module)
    wrapper_func = getattr(throwaway_module, wrapper_name)
    modified_function = wrapper_func()

    return modified_function


def _create_function_in_inner_module(function_source, module):
    try:
        exec(function_source, module.__dict__)
    except IndentationError as e:
        raise ValueError('There\'s a problem with the indentation. Maybe forgot to set indent_inner?') from e


def _modify_source(func, start='', end='', indent=0):
    if not start and not end:
        raise ValueError('Must supply code for at least one of "start" or "end" arguments.')

    func_source = _process_function_source(func)
    end_indented, start_indented = _process_wrapping_code(end, start)
    func_signature, func_body = _divide_source(func_source)

    if indent:
        func_body = _indent_lines(func_body, indent, _INDENT_STRING)

    modified_source = func_signature \
                      + start_indented \
                      + func_body \
                      + end_indented

    print(modified_source)
    return modified_source


def _divide_source(func_source):
    func_sig_matches = re.search(_FUNC_SIGNATURE_REGEX, func_source)
    func_sig_end_index = func_sig_matches.end()

    func_signature = func_source[:func_sig_end_index]
    if func_signature[-1].isspace():
        raise RuntimeError('This shouldn\'t happen - the regex should never return a signature ending with whitespace.')

    func_body = func_source[func_sig_end_index:].strip('\n')

    func_signature = func_signature + '\n'
    func_body = '\n' + func_body + '\n'

    return func_signature, func_body


def _process_wrapping_code(end, start):
    # added code will always have an indentation level of 1 - immediately under the function
    if start:
        start_indented = '\n'
        start_indented += _INDENT_STRING + ('\n' + _INDENT_STRING).join(start.splitlines())
        start_indented += '\n'
    else:
        start_indented = start

    if end:
        end_indented = '\n'
        end_indented += _INDENT_STRING + ('\n' + _INDENT_STRING).join(end.splitlines())
        end_indented += '\n'
    else:
        end_indented = end

    return end_indented, start_indented


def _process_function_source(func):
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

    if not all(s == ' ' for s in source_before_sig):
        raise RuntimeError('All of the text before the function signature should be whitespace.')

    func_indent_level = int(len(source_before_sig) / len(_INDENT_STRING))  # int to indicate level of indentation
    after_indent_index = func_indent_level * len(_INDENT_STRING)

    source_unindented_lines = []
    for line in func_source.splitlines(keepends=True):
        unindented = line[after_indent_index:]
        source_unindented_lines.append(unindented)

    source_unindented = ''.join(source_unindented_lines)
    return source_unindented


def _strip_leading_decorators(source_unindented):
    signature_regex = re.search(_FUNC_SIGNATURE_REGEX, source_unindented)
    sig_start_index = signature_regex.start()
    return source_unindented[sig_start_index:]


if __name__ == '__main__':
    def f():
        a = 8
        def g():
            print(a)
        return g

    g = f()
    extend_function(g, start='print()')
    g()


