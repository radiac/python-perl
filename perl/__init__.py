import builtins

from .console import replace_console
from .loader import install_loader

# Run automatic import of module loader, unless disabled
if not builtins.__dict__.get("__perl__disable_automatic_import", False):
    install_loader()

# If running in an interactive console, replace it with ours
if not builtins.__dict__.get("__perl__disable_automatic_console", False):
    replace_console()
