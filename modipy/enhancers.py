import inspect

from . import core


def typecheck(func):
    """
    This decorator injects runtime type-checking in the beginning of the function, according to the function's
    type annotations.
    Unannotated parameters are not typechecked.
    """
    func_annotations = func.__annotations__

    if not func_annotations:
        return func

    check_lines = []
    for arg_name, arg_type in func_annotations.items():
        check_lines.append('if not isinstance({arg_name}, {arg_type}): '
                           'raise TypeError("{arg_name} must be of type {arg_type}. Was of type: {{actual_type}}".format(actual_type=type({arg_name}).__name__))'
                           .format(arg_name=arg_name, arg_type=arg_type.__name__))
    checks = '\n'.join(check_lines)

    core.extend_function(func, start=checks)
    return func


def ignoreerror(error):
    code_for_error = _error_to_python_code(error)

    def dec(func):
        core.extend_function(func,
                             start='try:',
                             end='except {error}: pass'.format(error=code_for_error), indent_inner=1)
        return func

    return dec


def _error_to_python_code(error):
    is_exception_class = inspect.isclass(error) and issubclass(error, Exception)
    no_args_to_decorator = callable(error) and not is_exception_class
    if no_args_to_decorator:
        return Exception.__name__  # the default exception class

    elif issubclass(error, Exception):
        return error.__name__

    # got tuple of exceptions
    elif isinstance(error, tuple) and all(isinstance(o, Exception) for o in error):
        return '(' + ','.join(error) + ')'

    else:
        raise TypeError('Error must be an Exception class or a tuple of Exception classes.')
