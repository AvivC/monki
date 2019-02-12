import pytest

from modipy.enhancers import typecheck, ignoreerror


def test_typecheck_doesnt_raise_when_all_args_correct():
    @typecheck
    def func(a: str, b: int, output: list):
        output.append('In function')

    output = []
    func('abc', 10, output)  # shouldn't raise an error
    assert output == ['In function']


def test_typecheck_raises_error_on_incorrect_types():
    @typecheck
    def func(a: str, b: int, output: list, c: list):
        output.append('In function')

    output = []
    with pytest.raises(TypeError) as exc:
        func('abc', 10, output, 'this should be a list')
    assert "c must be of type list. Was of type: str" in str(exc)
    assert output == []


def test_typecheck_does_nothing_when_no_type_annotations():
    @typecheck
    def func(a, b, output):
        output.append('In function')

    output = []
    func({}, 'b', output)  # just random types. an exception shouldn't be raised
    assert output == ['In function']


def test_ignoreerror_with_specified_exception():
    @ignoreerror(RuntimeError)
    def func():
        raise RuntimeError('The world is ending!')

    func()  # the RuntimeError should be caught


def test_ignoreerror_when_subclass_is_raised():
    class MyError(RuntimeError):
        pass

    @ignoreerror(RuntimeError)
    def func():
        raise MyError('The world is ending!')

    func()  # the MyError should be caught
