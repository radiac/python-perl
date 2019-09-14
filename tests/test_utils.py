import builtins
import re

from perl.utils import re_match, reset_vars


def test_utils__reset_vars():
    builtins.__dict__["__perl__var__example"] = 1
    assert "__perl__var__example" in builtins.__dict__
    reset_vars()
    assert "__perl__var__example" not in builtins.__dict__


def test_utils__re_match():
    # Create a Match and sanity check it
    match = re.search(
        r"^(.+?) (?P<name1>.+?) (.+?) (?P<name2>.+?)$", "one two three four"
    )
    assert match.groups() == ("one", "two", "three", "four")
    assert match.groupdict() == {"name1": "two", "name2": "four"}

    returned_match = re_match(match)
    assert returned_match == match
    assert builtins.__dict__["__perl__var__1"] == "one"
    assert builtins.__dict__["__perl__var__2"] == "two"
    assert builtins.__dict__["__perl__var__3"] == "three"
    assert builtins.__dict__["__perl__var__4"] == "four"
    assert builtins.__dict__["__perl__var__name1"] == "two"
    assert builtins.__dict__["__perl__var__name2"] == "four"

    # Clean up builtins
    reset_vars()


def test_utils__re_match_global():
    """
    Match with global flag

    example::

        var =~ /foo/g
    """
    matches_iter = re.finditer(r"(.+?) ", "one two three four ")
    assert hasattr(matches_iter, "__iter__")
    matches = list(matches_iter)
    assert len(matches) == 4
    assert matches[0].groups() == ("one",)
    assert matches[1].groups() == ("two",)
    assert matches[2].groups() == ("three",)
    assert matches[3].groups() == ("four",)

    returned_matches_iter = re_match(re.finditer(r"(.+?) ", "one two three four "))
    assert hasattr(returned_matches_iter, "__iter__")
    returned_matches = list(returned_matches_iter)
    assert [m.groups() for m in matches] == [m.groups() for m in returned_matches]
