import builtins
import re
import sys
from importlib import invalidate_caches
from importlib.abc import SourceLoader
from importlib.machinery import FileFinder
from importlib.util import module_from_spec, spec_from_loader

from .translator import translate
from .utils import re_match, reset_vars


class PerlLoader(SourceLoader):
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def get_filename(self, name):
        return self.path

    def get_data(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = translate(f.readline)
        return data


def install_loader():
    """
    Install the import hook

    Once this has been run, the enhancements will be available in any imported code

    This will run automatically when the package is imported; to disable::

        builtins.__dict__["__perl__disable_automatic_import"] = True
    """
    # Set up import hook
    loader_details = PerlLoader, [".py"]
    sys.path_hooks.insert(0, FileFinder.path_hook(loader_details))
    sys.path_importer_cache.clear()
    invalidate_caches()

    # Inject dependencies for rewritten code
    builtins.__dict__["re"] = re
    builtins.__dict__["__perl__re_match"] = re_match
    builtins.__dict__["__perl__reset_vars"] = reset_vars


def load(module_name, filename):
    """
    Helper function to load the specified filename into the specified module name
    """
    loader = PerlLoader(module_name, filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module
