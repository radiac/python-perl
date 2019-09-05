========================
Perl as a Python package
========================

.. image:: https://travis-ci.org/radiac/python-perl.svg?branch=master
    :target: https://travis-ci.org/radiac/python-perl

.. image:: https://coveralls.io/repos/radiac/python-perl/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/radiac/python-perl?branch=master


Haven't you always dreamed of having the power of Perl at your fingertips when writing
Python?

Well, this package is proof that dreams can come true::

    >>> import perl
    >>> value = "Hello there"
    >>> if value =~ /^hello (.+?)$/i:
    ...     print("Found greeting:", $1)
    ...
    Found greeting: there
    >>> value =~ s/there/world/
    >>> print(value)
    Hello world


Note: This is very silly and probably shouldn't go anywhere near production code.

* Project site: http://radiac.net/projects/python-perl/
* Source code: https://github.com/radiac/python-perl


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

3.  Import it before importing any of your code which uses its syntax - usually in
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


Features
========

Regular expression matching
---------------------------

Syntax::

    val =~ /pattern/flags
    # or
    val =~ m/pattern/flags

where ``pattern`` uses `Python's regex syntax`_, and ``flags`` is a subset of the
characters ``AILMSXG``, which map Python's single character flags, plus ``g`` which
mimics the global flag from Perl.

When run without the global flag, the ``re.Match`` object is returned; any matched
groups will be available as numbered dollar variables, eg ``$1``, and named groups will
be available on ``$name``.

When run with the global flag, the list of ``re.Match`` objects will be returned. No
dollar variables will be set.

.. _Python's regex syntax: https://docs.python.org/3/library/re.html#regular-expression-syntax

Examples::

    # Case insensitive match
    value =~ /^foo (.+?) bar$/i
    print(f"Matched {$1}")

    # Use in a condition
    if value =~ /^foo (.+?) bar$/i:
        return $1

    # Use as a global
    matches = value =~ /foo (.+?) bar/gi;


Regular expression replacement
------------------------------

Syntax:

    val =~ s/pattern/replacement/flags

where ``pattern`` uses `Python's regex syntax`_, and ``flags`` is a subset of the
characters ``AILMSXG``, which map Python's single character flags, plus ``g`` which
mimics the global flag from Perl to replace all occurrences of the match.

Examples::

    # Case insensitive global replacement
    value =~ s/foo/bar/gi


Dollar variables
----------------

Syntax::

    $name
    $number

Dollar variables act like regular variables - they can be set and used as normal. They
are primarily intended for use with regular expressions - each regex will remove all
previous dollar variables, to avoid confusion as to whether they matched or not.


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
