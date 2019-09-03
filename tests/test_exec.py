import re

import pytest

from perl.translator import translate_string
from perl.utils import re_match, reset_vars


@pytest.fixture
def _globals():
    return {"re": re, "__perl__re_match": re_match, "__perl__reset_vars": reset_vars}


def test_match__value_present__returns_true(_globals):
    ldict = {"var": "one foo two"}
    src = translate_string("var =~ /foo/")
    result = eval(src, _globals, ldict)
    assert isinstance(result, re.Match)


def test_match__value_not_present__returns_false(_globals):
    ldict = {"var": "one two"}
    src = translate_string("var =~ /foo/")
    result = eval(src, _globals, ldict)
    assert result is None


def test_match__value_match__value_set(_globals):
    ldict = {"var": "one foo two"}
    src = translate_string("var =~ /(foo)/")
    result = eval(src, _globals, ldict)
    assert isinstance(result, re.Match)
    assert "__perl__var__1" in _globals["__builtins__"]
    assert _globals["__builtins__"]["__perl__var__1"] == "foo"
