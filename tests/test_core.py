import pytest
import monki


class TestWrappingFunction:
    """
    Tests for the basic functionality of wrapping a function with 'start' and/or 'end' code,
    with optionally indenting the inner code.
    """

    def test_adding_start_and_end_to_function(self):
        def func(outlist):
            outlist.append("middle")

        monki.patch(func, start='outlist.append("start")', end='outlist.append("end")')
        outlist = []
        func(outlist)
        assert outlist == ['start', 'middle', 'end']

    def test_adding_only_start_to_function(self):
        def func(outlist):
            outlist.append("middle")

        monki.patch(func, start='outlist.append("start")')
        outlist = []
        func(outlist)
        assert outlist == ['start', 'middle']

    def test_adding_only_end_to_function(self):
        def func(outlist):
            outlist.append("middle")

        monki.patch(func, end='outlist.append("end")')
        outlist = []
        func(outlist)
        assert outlist == ['middle', 'end']

    def test_indent_inner_code_by_wrapping_with_loop(self):
        def func(outlist):
            outlist.append("In loop " + str(i))  # the function should know about variable `i` after the injection

        monki.patch(func, start='for i in range(3):\n', end='outlist.append("Finished looping")', indent_inner=1)
        outlist = []
        func(outlist)
        assert outlist == ['In loop 0', 'In loop 1', 'In loop 2', 'Finished looping']

    def test_not_passing_code_to_inject_raises_error(self):
        def func():
            pass

        with pytest.raises(ValueError) as ex:
            monki.patch(func)
        assert 'Must supply code to inject or indent' \
               '.' in str(ex)

    def test_illegal_value_to_indent_inner_raises_typeerror(self):
        def func():
            pass

        error_message = 'indent_inner must be a boolean or a positive integer, to represent indentation level.'

        def _assert_illegal_indent_inner_raises_error(value):
            with pytest.raises(TypeError) as exc:
                monki.patch(func, start='pass', indent_inner=value)
            assert error_message in str(exc)

        _assert_illegal_indent_inner_raises_error(None)
        _assert_illegal_indent_inner_raises_error(-1)
        _assert_illegal_indent_inner_raises_error('XXX')
        _assert_illegal_indent_inner_raises_error('1')
        _assert_illegal_indent_inner_raises_error(2.5)

    def test_correct_indent_inner_parameter_options(self):
        for indent_option in {True, 1, 2, 10}:
            def func(outlist):
                outlist.append('in loop')

            monki.patch(func, start='for i in range(5): ', indent_inner=indent_option)
            outlist = []
            func(outlist)
            assert outlist == ['in loop'] * 5

    def test_incorrect_indentation_raises_error(self):
        def func(outlist):
            outlist.append('in loop')

        with pytest.raises(ValueError) as exc:
            monki.patch(func, start='for i in range(5): ', indent_inner=False)
        assert 'There\'s a problem with the indentation.' in str(exc)


class TestProcessingClosures:
    """
    Closure functions are treated a bit differently inside CPython, so they deserve
    different implementation details. These checks make sure they work correctly.
    """

    def test_processing_closure_function_no_args(self):
        def outer_function():
            some_list = [1, 2, 3]
            some_string = 'things'

            def my_closure():
                some_list.append(some_string)
                return some_list[-1]

            return my_closure

        closure = outer_function()
        monki.patch(closure, start='print("Beginning")', end='print("Ending")')
        assert closure() == 'things'

    def test_inner_indentation_in_closure(self):
        def outer_function():
            out_list = ['things']
            some_string = 'things'

            def my_closure():
                out_list.append(some_string)

            return my_closure, out_list

        closure, out_list = outer_function()
        monki.patch(closure, start='for i in range(5):', indent_inner=1)
        closure()
        assert out_list == ['things'] * 6

    def test_closures_that_originally_set_outer_names(self):
        def outer_function():
            a = 'outer_a'
            b = 'outer_b'

            def my_closure():
                a = 'inner_a'
                return a, b

            return my_closure

        closure = outer_function()
        monki.patch(closure, start='pass')
        a, b = closure()
        assert a == 'inner_a'
        assert b == 'outer_b'

    def test_extending_closure_with_setting_free_variable_raises_unsupported_exception(self):
        def outer_function():
            a = 'outer_a'
            b = 'outer_b'

            def my_closure():
                return a, b

            return my_closure

        closure = outer_function()

        with pytest.raises(ValueError) as exc:
            monki.patch(closure, start='a = "inner_a"')
        assert 'Setting variables from outer function in extension - currently not supported.' in str(exc)


class TestInjectingLines:
    """
    Tests for injecting lines into arbitrary line offsets inside the function.
    """

    def test_injecting_single_line(self):
        def func(outlist):
            outlist.append('Starting')  # 0
            outlist.append('Middle')    # 1
            outlist.append('Ending')    # 2
            return outlist

        monki.patch(func, insert_lines={2: 'outlist.append("Injected before end")'})
        outlist = []
        assert func(outlist) == ['Starting', 'Middle', 'Injected before end', 'Ending']

    def test_injecting_multiple_lines(self):
        def func(outlist):
            outlist.append('Starting')
            outlist.append('Middle')
            outlist.append('Ending')

        monki.patch(func, insert_lines={1: 'outlist.append("Injected before middle")', 2: 'outlist.append("Injected before end")'})
        outlist = []
        func(outlist)
        assert outlist == ['Starting', 'Injected before middle', 'Middle', 'Injected before end', 'Ending']

    def test_injecting_lines_in_multi_indent_func(self):
        def func(o):
            o.append('Before loop')                  # 0
            for i in range(2):                       # 1
                o.append('In loop')                  # 2
                o.append('In iteration: ' + str(i))  # 3
            o.append('Finished loop')                # 4
            return o

        monki.patch(func, insert_lines={0: "o.append('Beginning func')",
                                        1: "o.append('Starting loop')",
                                        3: "    o.append('Middle of iteration: ' + str(i))"})
        result = func([])
        assert result == ['Beginning func', 'Before loop', 'Starting loop', 'In loop',
                          'Middle of iteration: 0', 'In iteration: 0', 'In loop', 'Middle of iteration: 1', 'In iteration: 1', 'Finished loop']

    def test_injecting_lines_and_also_wrapping(self):
        def func(o):
            o.append('Before loop')                  # 0
            for i in range(2):                       # 1
                o.append('In loop')                  # 2
                o.append('In iteration: ' + str(i))  # 3
            o.append('Finished loop')                # 4
            return o

        monki.patch(func,
                    start="o.append('Beginning func')",
                    end=r"o.append('This shouldn\'t enter list - injected after the return statement')",
                    insert_lines={
                                  1: "o.append('Starting loop')",
                                  3: "    o.append('Middle of iteration: ' + str(i))"}
                    )
        result = func([])
        assert result == ['Beginning func', 'Before loop', 'Starting loop', 'In loop',
                          'Middle of iteration: 0', 'In iteration: 0', 'In loop', 'Middle of iteration: 1', 'In iteration: 1',
                          'Finished loop']


class TestIndentingLines:
    """
    Tests for indenting selected lines in the processed function.
    This allows for cool stuff, such as moving lines inside loops and such.
    """

    @staticmethod
    def _make_func():
        def func():
            o = list()                        # 0
            o.append('Starting')              # 1
            o.append('Iteration: ' + str(i))  # 2
            o.append('Ending')                # 3
            return o
        return func

    def test_with_indents_as_list(self):
        f = self._make_func()
        monki.patch(f, insert_lines={2: "for i in range(3):"}, indent_lines=[2])
        result = f()
        assert result == ['Starting', 'Iteration: 0', 'Iteration: 1', 'Iteration: 2', 'Ending']

    def test_with_indents_as_dict_level_1(self):
        f = self._make_func()
        monki.patch(f, insert_lines={2: "for i in range(3):"}, indent_lines={2: 1})
        result = f()
        assert result == ['Starting', 'Iteration: 0', 'Iteration: 1', 'Iteration: 2', 'Ending']

    def test_with_indents_as_dict_level_3(self):
        f = self._make_func()
        monki.patch(f, insert_lines={2: "for i in range(3):"}, indent_lines={2: 3})
        result = f()
        assert result == ['Starting', 'Iteration: 0', 'Iteration: 1', 'Iteration: 2', 'Ending']

    def test_indenting_with_injecting_and_wrapping(self):
        def func(o):
            o.append('Before loop')  # 0
            for i in range(2):  # 1
                o.append('In loop')  # 2
                o.append('In iteration: ' + str(i))  # 3
            o.append('Finished loop')  # 4
            o.append('This line should never run')  # 5
            return o

        # injecting "if False:" before line 5 and indenting line 5 should make it not run!
        monki.patch(func,
                    start="o.append('Beginning func')",
                    end=r"o.append('This shouldn\'t enter list - injected after the return statement')",
                    insert_lines={
                        1: "o.append('Starting loop')",
                        3: "    o.append('Middle of iteration: ' + str(i))",
                        5: "if False:"},
                    indent_lines=[5]
                    )

        result = func([])
        assert result == ['Beginning func', 'Before loop', 'Starting loop', 'In loop',
                          'Middle of iteration: 0', 'In iteration: 0', 'In loop', 'Middle of iteration: 1',
                          'In iteration: 1',
                          'Finished loop']

    def test_input_validation(self):
        error_message = 'indent_lines must be a list of lines to indent or a dict of line_number => indent_level'
        f = self._make_func()
        with pytest.raises(TypeError) as exc:
            monki.patch(f, insert_lines={2: "for i in range(3):"}, indent_lines=2)  # int is illegal input
        assert error_message in str(exc)
