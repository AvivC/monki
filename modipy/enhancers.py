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
