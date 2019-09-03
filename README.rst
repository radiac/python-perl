=======================
Perl as a Python module
=======================

Haven't you always dreamed of having the power of Perl at your fingertips when writing
Python?

Well, this module is proof that dreams can come true::

    >>> import perl
    >>> value = "Hello there"
    >>> if value =~ /^hello (.+?)$/i:
    ...     print("Found greeting:", $1)
    ...
    Found greeting: there
    >>> value =~ s/there/world/
    >>> print(value)
    Hello world


Installation
============

This requires Python 3.7 or later.


Usage
=====

The module needs to be loaded before Python tries to read code which uses these
enhancements. There are therefore four different ways to use this module:

1.  Pass it to Python on the command line::

        python3.7 -m perl myscript.py

2.  Set it on your script's shebang::

        #!/usr/bin/python3.7 -mperl

3.  Import it before importing any of your code which uses it's syntax - usually in
    your ``__init__.py``::

        import perl

    .. note::

        You only need to import it once in your project.

        However, because Python needs to read the whole file before it can run the
        import, you cannot use ``perl``'s functionality in the same file where you
        ``import perl``.

4.  Use it on the Python interactive shell (REPL)::

        $ python3.7
        >>> import perl

    or::

        $ python3.7 -m perl


Contributing
============

During development, install in a virtual environment::

    mkdir python-perl
    cd python-perl
    git clone <path-to-repo> repo
    virtualenv --python=python3.7 venv
    . venv/bin/activate
    cd repo
    pip install -r requirements.txt


To run tests::

    cd path/to/repo
    . ../venv/bin/activate
    pytest


To run the example, use one of the following::

    $ ./example.py
    $ python3.7 -m perl example.py
    $ python3.7 example_importer.py
