from perl.translator import translate_string


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
