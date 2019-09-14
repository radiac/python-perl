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


def test_translate__replace():
    assert (
        translate_string("var =~ s/foo/bar/")
        == "var = __perl__reset_vars() or re.sub(r'foo', r'bar', var, count=1)"
    )


def test_translate__replace_with_backref():
    assert (
        translate_string("var =~ s/^foo (.+?) bar/foo $1 bar/")
        == "var = __perl__reset_vars() or re.sub(r'^foo (.+?)', r'foo \\g<1> bar')"
    )


def test_translate__replace_with_named_backref():
    assert translate_string("var =~ s/^foo (?P<named>.+?) bar/foo $named bar/") == (
        "var = __perl__reset_vars() or "
        "re.sub(r'^foo (?P<named>.+?) bar', r'foo \\g<named> bar')"
    )


def test_translate__replace_all():
    assert (
        translate_string("var =~ s/foo/bar/g")
        == "var = __perl__reset_vars() or re.sub(r'foo', r'bar', var)"
    )
