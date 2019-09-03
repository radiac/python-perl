#!/usr/bin/python3.7 -mperl
"""
Example use of the perl module

Run with one of::

    $ ./example.py
    $ python3.7 -m perl example.py
    $ python3.7 example_importer.py
"""
a = "Hello World"

a =~ s/world/there/i
print(f"Output:{a}:")

a =~ /Hello (.+)/
print(f"Match:{$1}:")
