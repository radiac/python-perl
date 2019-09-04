"""
Utility functions for translated code
"""
import builtins
import re


def reset_vars():
    """
    Clear perl vars
    """
    for var in list(builtins.__dict__.keys()):
        if var.startswith("__perl__var__"):
            del builtins.__dict__[var]


def re_match(match):
    """
    Handle a possible Match
    """
    # Clear vars so they don't persist between matches
    reset_vars()

    if isinstance(match, re.Match):
        # Get named matches
        matches = match.groupdict()

        # Add positional matches (groupdict returns a copy, so this'll be safe)
        matches.update({n + 1: val for n, val in enumerate(match.groups())})

        # Store values on builtins - no way to modify the local vars of the caller
        for key, val in matches.items():
            builtins.__dict__[f"__perl__var__{key}"] = val

    return match
