"""
Main translator - converts Perl-enhanced Python into regular Python
"""
import io
import re
import tokenize
from enum import Enum
from typing import Optional, Tuple

from cached_property import cached_property

from .token import Token


# List of standard Python modifiers, plus the g modifier from Perl
MODIFIERS = set("AILMSXG")


class ParseError(Exception):
    pass


class CollectState(Enum):
    WAITING = 0
    ACTIVE = 1
    COMPLETE = 2


class Op(Enum):
    MATCH = 1
    REPLACE = 2


class Modifier(Enum):
    ASCII = "A"
    IGNORECASE = "I"
    LOCALE = "L"
    MULTILINE = "M"
    DOTALL = "S"
    VERBOSE = "X"
    GLOBAL = "G"


class PerlTranslator:
    def translate(self, readline):
        # Tokenize into token chain
        start_token = Token.from_stream(readline)

        # Loop through the token chain
        next_tok: Token = start_token
        tok: Token = None
        while next_tok:
            # Advance the token
            tok = next_tok
            next_tok = tok.next

            for collector in self.collectors:
                replacement = collector(tok)
                if replacement:
                    new_start, next_tok = replacement
                    if not new_start.prev:
                        # Start token is now at the start of the chain
                        start_token = new_start
                    break

        # Render tokens
        tok = start_token
        while tok:
            yield tok.rendered
            tok = tok.next

    @cached_property
    def collectors(self):
        """
        Find the collectors which will do the translation
        """
        collectors = [
            getattr(self, name) for name in dir(self) if name.startswith("collect_")
        ]
        return collectors

    def collect_fstring(self, tok) -> Optional[Tuple[Token, Optional[Token]]]:
        """
        Translate an fstring - replace dollar strings
        """
        if not (tok.type == tokenize.STRING and tok.string.startswith("f")):
            return None

        fstring = tok.rendered()

        translated = []
        ptr = 0
        while True:
            # TODO: this is very flimsy and doesn't deal with escapes
            start = fstring.find("{", ptr)
            if start == -1:
                break
            end = fstring.find("}", start)
            if end == -1:
                break

            # Copy fstring from ptr up to and including open bracket
            translated.append(fstring[ptr : start + 1])

            # Python excludes the brackets
            python = fstring[start + 1 : end]
            translated.append(translate_string(python))
            ptr = end

        # Add on anything remaining
        translated.append(fstring[ptr:])

        replacement = tok.translate("".join(translated), end=tok)
        next_tok = replacement.next
        return replacement, next_tok

    def collect_dollar(self, tok) -> Optional[Tuple[Token, Optional[Token]]]:
        """
        Collect a $string or $number
        """
        # Check for dollar
        if not (tok.type == tokenize.ERRORTOKEN and tok.string == "$"):
            return None
        dollar = tok

        # Check the next token is a string or number,
        # and they weren't separated by a space
        tok = tok.next
        if (
            not tok
            or tok.type not in [tokenize.NAME, tokenize.NUMBER]
            or tok.rendered[0].isspace()
        ):
            return None

        # We've found one
        next_tok = tok.next
        replacement = dollar.translate(f"__perl__var__{tok.string}", end=tok)
        return replacement, next_tok

    def collect_regex(self, tok):
        """
        Collect regex matches:

            var =~ /match/flags
            var =~ s/match/replace/flags
        """
        # Look for ``=~``
        if not (tok.type == tokenize.OP and tok.string == "="):
            return
        start = tok
        tok = tok.next
        if not (tok.type == tokenize.OP and tok.string == "~"):
            return
        tok = tok.next

        # Found ``=~`` - find preceding ``var`` and its leading whitespace
        start = start.prev
        if not start or not start.type == tokenize.NAME:
            # Didn't find ``var =~``
            return
        variable: str = start.string
        whitespace: str = start.rendered[: -len(variable)]

        # Look for start of match or replacement
        # Might be getting:
        #  /../
        #  m/../
        #  s/../../
        op: Op
        if tok.type == tokenize.NAME and tok.string in ["m", "s"]:
            # Explicit match or replace
            if tok.string == "m":
                op = Op.MATCH
            else:
                op = Op.REPLACE
            tok = tok.next

            # Now we need the ``/``
            if not (tok.type == tokenize.OP and tok.string == "/"):
                # Didn't find the pattern start
                return

        elif tok.type == tokenize.OP and tok.string == "/":
            # Implicit match
            op = Op.MATCH

        else:
            # Not a valid op
            # ++ TODO - failing here due to whitespace?
            return
        # Ignore the leading /
        tok = tok.next

        # Now the match - collect everything up to the next ``/``
        tok, match = tok.get_to_slash()
        if not tok:
            # We ran out of tokens
            return
        # Ignore the trailing /
        tok = tok.next

        # Now the replace, if we're replacing
        if op == Op.REPLACE:
            tok, replace = tok.get_to_slash()
            if not tok:
                return
            tok = tok.next

        # Now the flags
        is_global = False
        flags = []
        if tok.type == tokenize.NAME:
            # May have found a modifier
            modifiers = set(tok.string.upper())
            if modifiers.difference(MODIFIERS):
                # Invalid modifier
                return

            # Found modifier
            if Modifier.GLOBAL.value in modifiers:
                is_global = True
                modifiers.remove(Modifier.GLOBAL.value)
            flags = [Modifier(modifier) for modifier in modifiers]

            # Advance
            tok = tok.next

        # Render the regular expression

        # Build string parts
        match_str = "".join([t.rendered for t in match])
        if flags:
            flags_ops = " | ".join([f"re.{flag.value}" for flag in flags])
            flags_str = f", flags={flags_ops}"
        else:
            flags_str = ""

        # Build ops
        if op == Op.MATCH:
            # Pass the match into our code so we can set vars
            python = (
                f"{whitespace}__perl__re_match("
                f"re.{'finditer' if is_global else 'search'}"
                f"(r'{match_str}', {variable}{flags_str})"
                ")"
            )

        else:
            # Build replace  and covert any backrefs
            replace_str = "".join([t.rendered for t in replace])
            replace_str = re.sub(r"\$(\w+)", r"\\g<\g<1>>", replace_str)

            if is_global:
                # By default the count is unlimited
                count = ""
            else:
                # Not global, specify one
                count = ", count=1"

            # Regex needs to reset the vars first in case it's a None
            python = (
                f"{whitespace}{variable} = __perl__reset_vars() or "
                f"re.sub(r'{match_str}', r'{replace_str}', {variable}"
                f"{count}{flags_str})"
            )

        # We've found one
        replacement = start.translate(python, end=tok.prev)

        # Return replacement start and one after the end
        return replacement, tok


def translate(src_generator):
    dest_generator = PerlTranslator().translate(src_generator)
    return "".join(dest_generator)


def translate_string(source):
    source_stream = io.StringIO(source).readline
    translated = translate(source_stream)
    return translated
