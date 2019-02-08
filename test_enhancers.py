import pytest

from modipy.enhancers import typecheck


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