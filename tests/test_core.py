import pytest
import modipy


def test_adding_start_and_end_to_function():
    def func(outlist):
        outlist.append("middle")

    modipy.extend_function(func, start='outlist.append("start")', end='outlist.append("end")')
    outlist = []
    func(outlist)
    assert outlist == ['start', 'middle', 'end']


def test_adding_only_start_to_function():
    def func(outlist):
        outlist.append("middle")

    modipy.extend_function(func, start='outlist.append("start")')
    outlist = []
    func(outlist)
    assert outlist == ['start', 'middle']


def test_adding_only_end_to_function():
    def func(outlist):
        outlist.append("middle")

    modipy.extend_function(func, end='outlist.append("end")')
    outlist = []
    func(outlist)
    assert outlist == ['middle', 'end']


def test_indent_inner_code_by_wrapping_with_loop():
    def func(outlist):
        outlist.append("In loop " + str(i))  # the function should know about variable `i` after the injection

    modipy.extend_function(func, start='for i in range(3):\n', end='outlist.append("Finished looping")', indent_inner=1)
    outlist = []
    func(outlist)
    assert outlist == ['In loop 0', 'In loop 1', 'In loop 2', 'Finished looping']


def test_passing_no_start_or_end_raises_exception():
    def func():
        pass

    with pytest.raises(ValueError) as ex:
        modipy.extend_function(func)
    assert 'Must supply code for at least one of "start" or "end" arguments.' in str(ex)


def test_processing_closure_function_no_args():
    def outer_function():
        some_list = [1, 2, 3]
        some_string = 'things'

        def my_closure():
            some_list.append(some_string)
            return some_list[-1]

        return my_closure

    closure = outer_function()
    modipy.extend_function(closure, start='print("Beginning")', end='print("Ending")')
    assert closure() == 'things'


def test_inner_indentation_in_closure():
    def outer_function():
        out_list = ['things']
        some_string = 'things'

        def my_closure():
            out_list.append(some_string)

        return my_closure, out_list

    closure, out_list = outer_function()
    modipy.extend_function(closure, start='for i in range(5):', indent_inner=1)
    closure()
    assert out_list == ['things'] * 6


def test_closures_that_originally_set_outer_names():
    def outer_function():
        a = 'outer_a'
        b = 'outer_b'

        def my_closure():
            a = 'inner_a'
            return a, b

        return my_closure

    closure = outer_function()
    modipy.extend_function(closure, start='pass')
    a, b = closure()
    assert a == 'inner_a'
    assert b == 'outer_b'


def test_extending_closure_with_setting_free_variable_raises_unsupported_exception():
    def outer_function():
        a = 'outer_a'
        b = 'outer_b'

        def my_closure():
            return a, b

        return my_closure

    closure = outer_function()

    with pytest.raises(ValueError) as exc:
        modipy.extend_function(closure, start='a = "inner_a"')
    assert 'Setting variables from outer function in extension - currently not supported.' in str(exc)


def test_correct_indent_inner_parameter_options():
    for indent_option in {True, 1, 2, 10}:
        def func(outlist):
            outlist.append('in loop')

        modipy.extend_function(func, start='for i in range(5): ', indent_inner=indent_option)
        outlist = []
        func(outlist)
        assert outlist == ['in loop'] * 5


def test_incorrect_indentation_raises_error():
    def func(outlist):
        outlist.append('in loop')

    with pytest.raises(ValueError) as exc:
        modipy.extend_function(func, start='for i in range(5): ', indent_inner=False)
    assert 'There\'s a problem with the indentation.' in str(exc)
