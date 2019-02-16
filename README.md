# Monki

Patch functions at runtime, the easy way.

## Installation

    pip install monki

## Basic usage

We want to patch the following function:

    def func():
        print('First')   # line 0
        print('Second')  # line 1
        print('Third')   # line 2

Different ways to patch it:

    import monki

    # Add code at beginning or end
    
    monki.patch(func, start="print('Starting')", end="print('Ending')")
    func()
        >>> 'Starting'
        >>> 'First'
        >>> 'Second'
        >>> 'Third'
        >>> 'Ending'

    # Insert lines at any offset
    
    monki.patch(func, insert={1: "print('Injected line')", 2: "print('Another injection')"})
    func()
        >>> 'First'
        >>> 'Injected line'
        >>> 'Second'
        >>> 'Another injection'
        >>> 'Third'

    # Let's patch a loop inside the function!
    # To do so we need to insert the loop and indent a line to go inside it.
    
    monki.patch(func, insert={1: "for i in range(3):"}, indent_lines=[1])
    func()
        >>> 'First'
        >>> 'Second'
        >>> 'Second'
        >>> 'Second'
        >>> 'Third'

## Limitations

* Currently you cannot patch the same function twice
* Some edge cases will not work with closure functions
* Will probably only work on CPython 3+. Currently only tested on CPython 3.7