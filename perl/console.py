import sys
from code import InteractiveConsole
from tokenize import TokenError

from .translator import translate_string


class PerlConsole(InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", replacing=False):
        super().__init__(locals=locals, filename=filename)
        self.replacing = True

    def interact(self, *args, **kwargs):
        super().interact(*args, **kwargs)

        # When replacing a console, exit from that too
        if self.replacing:
            sys.exit()

    def runsource(self, source, *args, **kwargs):
        try:
            translated = translate_string(source)
        except TokenError as e:
            if e.args[0] == "EOF in multi-line statement":
                return True
            raise
        return super().runsource(translated, *args, **kwargs)


def replace_console():
    """
    If we detect a console, start our own
    """
    if hasattr(sys, "ps1"):
        # Use console globals as context
        context = sys.modules["__main__"].__dict__
        console = PerlConsole(context, replacing=True)

        # Start and exit silently
        console.interact(banner="", exitmsg="")
