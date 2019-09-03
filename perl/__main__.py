"""
Support being executed directly

Handle being called from the shell as::

    $ python -m perl script.py

or from a shebang as::

    #!/path/to/python3.7 -mperl
"""
import argparse

from .console import PerlConsole
from .loader import load

# Find and load the Python script
parser = argparse.ArgumentParser(prog="python -m perl")
parser.add_argument(
    dest="filename", metavar="filename.py", nargs="?", help="The file to run"
)
args = parser.parse_args()

if args.filename:
    load("__main__", args.filename)

else:
    console = PerlConsole()
    console.interact()
