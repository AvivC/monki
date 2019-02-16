import collections
import re
import inspect
from types import CodeType, ModuleType


_FUNC_SIGNATURE_REGEX = r'def (\w+)\s*\(((\s|.)*?)\)\s*:'
_INDENT_STRING = '    '


def patch(func, start='', end='', insert_lines=None, indent_lines=None, indent_inner=False):
    """
    Easily modify a function's code at runtime.
    Can be called at most once on a single function.

    Consider we want to patch the following function:

    def func():
        print('First')   # line 0
        print('Second')  # line 1
        print('Third')   # line 2

    Examples of different ways to patch it:

        # Wrap the function with start and end code
        monki.patch(func, start="print('Starting')", end="print('Ending')")
        func()
            >>> 'Starting'
            >>> 'First'
            >>> 'Second'
            >>> 'Third'
            >>> 'Ending'

        # Inject lines at any offset
        monki.patch(func, insert={1: "print('Injected line')", 2: "print('Another injection')"})
        func()
            >>> 'First'
            >>> 'Injected line'
            >>> 'Second'
            >>> 'Another injection'
            >>> 'Third'

        # Indent existing lines. Let's use that along with injection in order to create a loop!
        # This injects the `for` before line 1, and indents line 1 so it's inside the loop.
        monki.patch(func, insert={1: "for i in range(3):"}, indent_lines=[1])
        func()
            >>> 'First'
            >>> 'Second'
            >>> 'Second'
            >>> 'Second'
            >>> 'Third'

    :param func: The function to patch.
    :param start: Code to inject in the beginning, right after the signature.
    :param end: Code to inject as the last line of the function.
    :param insert_lines:
        A dict of line number => code to inject.
        The code will be injected before the line number in the original code.
    :param indent_lines:
        A list of line numbers or a dictionary of line number => indent level.
        Used to indent specific lines.
    :param indent_inner:
        An int to indicate indentation level or a boolean (True is indent level of 1).
        Indents all of the original code inside the function
    """

    indent_inner, indent_lines, insert_lines = _validate_arguments(indent_inner, indent_lines, insert_lines)
    modified_source = _modify_source(func, start, end, insert_lines, indent_inner, indent_lines)
    _replace_code(func, modified_source)


def _validate_arguments(indent_inner, indent_lines, insert):
    if indent_inner is True:
        indent_inner = 1
    elif indent_inner is False:
        indent_inner = 0
    elif not (isinstance(indent_inner, int) and indent_inner >= 0):
        raise TypeError('indent_inner must be a boolean or a positive integer, to represent indentation level.')

    if isinstance(indent_lines, list):
        dict_indent_lines = {line_num: 1 for line_num in indent_lines}
    elif isinstance(indent_lines, dict):
        dict_indent_lines = indent_lines
    elif indent_lines is None:
        dict_indent_lines = {}
    else:
        raise TypeError('indent_lines must be a list of lines to indent or a dict of line_number => indent_level')

    insert = insert or {}

    return indent_inner, dict_indent_lines, insert


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

    closure_signature, closure_body_lines = _divide_source(modified_source)
    closure_body_lines = _indent_source_lines(closure_body_lines, indent_level=1)
    closure_body = '\n'.join(line.code for line in closure_body_lines)
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


_SourceLine = collections.namedtuple('SourceLine', ['code', 'number'])


def _modify_source(func, start, end, insert_lines, indent_inner, indent_lines):
    if not any([start, end, insert_lines]):
        raise ValueError('Must supply code to inject or indent.')

    func_source = _clean_function_source(func)

    func_signature, func_body_lines = _divide_source(func_source)

    if indent_inner:
        func_body_lines = _indent_source_lines(func_body_lines, indent_inner)

    _validate_no_collisions_between_wrappers_and_inserts(end, func_body_lines, insert_lines, start)

    if start:
        insert_lines[0] = start
    if end:
        # if we want to add code at the end, we need a blank line to add the code _before_ of
        # TODO: Tests seem to pass without this line - figure this out
        # func_body += '\n\n'
        # last_line_index = len(func_body.splitlines()) - 1
        last_line_index = len(func_body_lines)
        func_body_lines.append(_SourceLine('', last_line_index))
        insert_lines[last_line_index] = end

    end, start, insert_lines = _indent_injected_code(end, start, insert_lines)
    func_body = _process_body(insert_lines, func_body_lines, indent_lines)

    # modified_source = func_signature + start + func_body + end
    modified_source = func_signature + func_body

    return modified_source


def _indent_source_lines(func_body_lines, indent_level):
    return [_SourceLine(_indent_code(line.code, indent_level), line.number)
            for line in func_body_lines]


def _validate_no_collisions_between_wrappers_and_inserts(end, func_body, insert_lines, start):
    # TODO: Probably refactor to have this in the central validator function
    if (0 in insert_lines) and start:
        raise ValueError('Can\'t both insert line at index 0 and set \'start\' argument')
    if (len(func_body) in insert_lines) and end:
        raise ValueError('Can\'t both insert line on the last index (+1) and set \'end\' argument')


def _process_body(insert_lines, func_body_lines, indent_lines):
    # body_lines = list(filter(lambda line: line, func_body.splitlines()))  # remove empty lines
    processed_lines = []

    for line, linenum in func_body_lines:
        indent_line = linenum in indent_lines
        if indent_line:
            indent_level = indent_lines[linenum]
            line = _indent_code(line, indent_level)

        inject_line = linenum in insert_lines
        if inject_line:
            line_to_inject = insert_lines[linenum]
            processed_lines.append(line_to_inject)

        processed_lines.append(line)

    func_body = '\n'.join(processed_lines)
    # func_body = os.linesep.join(processed_lines)
    return func_body


def _divide_source(func_source):
    func_sig_matches = re.search(_FUNC_SIGNATURE_REGEX, func_source)
    func_sig_end_index = func_sig_matches.end()

    func_signature = func_source[:func_sig_end_index]
    if func_signature[-1].isspace():
        raise AssertionError('This shouldn\'t happen - the regex should never return a signature ending with whitespace.')

    func_signature = func_signature + '\n'

    func_body = func_source[func_sig_end_index:].strip('\n')
    # func_body = '\n' + func_body + '\n'
    func_body = func_body
    body_lines = [_SourceLine(code, linenum) for linenum, code in enumerate(func_body.splitlines())]

    return func_signature, body_lines
    # return func_signature, '\n'.join(line.code for line in body_lines)
    # return func_signature, func_body


def _indent_injected_code(end, start, insert_lines):
    # added code will always have an indentation level of 1 - immediately under the function
    start_indented = _indent_code(start, indent_level=1)
    end_indented = _indent_code(end, indent_level=1)
    insert_lines = {linenum: _indent_code(code, indent_level=1) for linenum, code in insert_lines.items()}

    return end_indented, start_indented, insert_lines


# def _indent_line(code):
#     # TODO: probably pretty much the same code and _indent_lines, consider merging the two
#     if code:
#         start_indented = '\n'
#         start_indented += _INDENT_STRING + ('\n' + _INDENT_STRING).join(code.splitlines())
#         start_indented += '\n'
#     else:
#         start_indented = code
#     return start_indented


def _clean_function_source(func):
    func_source = inspect.getsource(func)
    func_source = _unindent_source(func_source)
    func_source = _strip_leading_decorators(func_source)
    return func_source


def _indent_code(code, indent_level):
    relative_indent_string = indent_level * _INDENT_STRING
    return '\n' + relative_indent_string + ('\n' + relative_indent_string).join(code.splitlines()) + '\n'


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
