from perl.translator import translate_string


def test_translate__match():
    assert (
        translate_string("var =~ /foo/") == "__perl__re_match(re.search(r'foo', var))"
    )


def test_translate__match_all():
    assert (
        translate_string("var =~ /foo/g")
        == "__perl__re_match(re.finditer(r'foo', var))"
    )


def test_translate__escaped():
    assert (
        translate_string(r"var =~ /foo\/bar/")
        == "__perl__re_match(re.search(r'foo/bar', var))"
    )


def test_translate__if_match_with_brackets():
    assert (
        translate_string(
            """
var = "value"
if (var =~ /l/):
    print($1)
"""
        )
        == """
var = "value"
if (__perl__re_match(re.search(r'l', var))):
    print(__perl__var__1)
"""
    )


def test_translate__if_match_without_brackets():
    assert (
        translate_string(
            """
var = "value"
if var =~ /l/:
    print($1)
"""
        )
        == """
var = "value"
if __perl__re_match(re.search(r'l', var)):
    print(__perl__var__1)
"""
    )


def test_translate__match_assign():
    assert (
        translate_string(r"match = var =~ /foo/")
        == "match = __perl__re_match(re.search(r'foo', var))"
    )
