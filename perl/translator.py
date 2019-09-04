import io
import tokenize
from enum import Enum

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
    def __init__(self, *args, **kwargs):
        self.clear()
        return super().__init__(*args, **kwargs)

    def reset(self):
        for token_str in self.buffer:
            yield token_str

        self.clear()

    def clear(self):
        self.buffer = []
        self.dollar = False
        self.variable = None
        self.equals = False
        self.tilde = False
        self.op = None
        self.collecting_match = CollectState.WAITING
        self.match = []
        self.collecting_replace = CollectState.WAITING
        self.replace = []
        self.collecting_modifiers = CollectState.WAITING
        self.flags = []
        self.is_global = False

    def untokenize(self, tok):
        """
        The standard tokenize.untokzenise does not preserve whitespace, so this uses
        the full token to find the whitespace around the token string
        """
        # Extract start and end and prepare line for value extraction
        absolute_start_line, start_col = tok.start
        absolute_end_line, end_col = tok.end
        lines = tok.line.splitlines(keepends=True)

        # Adjust line numbers
        # Line numbers are 1-indexed, but ``lines`` is 0-indexed
        # ``tok.line`` starts at start_line
        end_line = absolute_end_line - absolute_start_line
        start_line = 0

        # Skip empty
        if not lines or (start_line == end_line and start_col == end_col):
            return ""

        # Find any preceding whitespace missed from the last token
        # Use the absolute line numbers
        buffer = []
        if self.last_line != absolute_start_line:
            # We're on a new line
            self.last_col = 0
        if self.last_col < start_col:
            # Found missing whitespace, collect
            buffer.append(lines[0][self.last_col : start_col])
        self.last_line = absolute_end_line
        self.last_col = end_col

        # Extract token with whitespace
        if start_line == end_line:
            # Single line handles differently
            buffer.append(lines[start_line][start_col:end_col])
        else:
            # Multiple lines
            buffer.append(lines[start_line][start_col:])
            for line_num in range(start_line + 1, end_line):
                buffer.append(lines[line_num])
            buffer.append(lines[end_line][:end_col])

        return "".join(buffer)

    def translate(self, readline):
        self.last_line = 1
        self.last_col = 0
        self.clear()

        for tok in tokenize.generate_tokens(readline):
            # Get token value with whitespace
            tok.original = self.untokenize(tok)
            self.buffer.append(tok.original)

            #
            # Add f-string support
            #

            if tok.type == tokenize.STRING and tok.string.startswith("f"):
                # Replace token
                self.buffer.pop()
                fstring = self.translate_fstring(tok.original)

                self.buffer.append(fstring)

                # Nothing else uses STRING, we're safe to return it
                yield from self.reset()
                continue

            #
            # Convert $1 (as long as we're not collecting)
            #

            if self.collecting_match != CollectState.ACTIVE:
                if tok.type == tokenize.ERRORTOKEN and tok.string == "$":
                    self.dollar = True
                    continue
                if self.dollar:
                    # Last token was a dollar. Check this one's a name or number,
                    # and they weren't separated by whitespace
                    if (
                        tok.type == tokenize.NAME or tok.type == tokenize.NUMBER
                    ) and not tok.original[0].isspace():
                        yield f"__perl__var__{tok.string}"
                        self.clear()
                    else:
                        yield from self.reset()
                    continue

            #
            # Convert regex
            #

            if not self.variable:
                if tok.type == tokenize.NAME:
                    # Store with any leading whitespace - we'll need that when rendering
                    self.variable = tok.original
                else:
                    yield from self.reset()
                continue

            if not self.equals:
                if tok.type == tokenize.OP and tok.string == "=":
                    self.equals = True
                elif tok.type == tokenize.NAME:
                    # We may have had a false start, eg ``if x =~``
                    self.buffer.pop()
                    yield from self.reset()
                    self.variable = tok.original
                    self.buffer.append(tok.original)
                else:
                    yield from self.reset()

                continue

            if not self.tilde:
                if tok.type == tokenize.OP and tok.string == "~":
                    self.tilde = True
                elif tok.type == tokenize.NAME:
                    # We may have had a false start, eg ``m = x =~`
                    self.buffer.pop()
                    yield from self.reset()
                    self.variable = tok.original
                    self.buffer.append(tok.original)
                else:
                    yield from self.reset()
                continue

            # Might be getting:
            #  /../
            #  m/../
            #  s/../../

            if not self.op:
                if tok.type == tokenize.NAME and tok.string in ["m", "s"]:
                    if tok.string == "m":
                        self.op = Op.MATCH
                    else:
                        self.op = Op.REPLACE
                elif tok.type == tokenize.OP and tok.string == "/":
                    self.op = Op.MATCH
                    self.collecting_match = CollectState.ACTIVE
                else:
                    # Not a valid op
                    yield from self.reset()
                continue

            # If we're not collecting the match yet, expect a /
            if self.collecting_match == CollectState.WAITING:
                if tok.type == tokenize.OP and tok.string == "/":
                    self.collecting_match = CollectState.ACTIVE
                else:
                    yield from self.reset()
                continue

            if self.collecting_match == CollectState.ACTIVE:
                # Check for close
                if tok.type == tokenize.OP and tok.string == "/":
                    if len(self.match) > 0 and self.match[-1] == "\\":
                        # It was escaped
                        self.match.pop()
                        self.match.append(tok.string)
                    else:
                        # Match closed
                        self.collecting_match = CollectState.COMPLETE

                        if self.op == Op.REPLACE:
                            self.collecting_replace = CollectState.ACTIVE
                        else:
                            self.collecting_modifiers = CollectState.ACTIVE
                else:
                    self.match.append(tok.string)
                continue

            if self.collecting_replace == CollectState.ACTIVE:
                # Check for close
                if tok.type == tokenize.OP and tok.string == "/":
                    if len(self.replace) > 0 and self.replace[-1] == "\\":
                        # It was escaped
                        self.replace.pop()
                        self.replace.append(tok.string)
                    else:
                        # Replace close
                        self.collecting_replace = CollectState.COMPLETE
                        self.collecting_modifiers = CollectState.ACTIVE
                else:
                    self.replace.append(tok.string)
                continue

            if self.collecting_modifiers == CollectState.ACTIVE:
                if tok.type == tokenize.NAME:
                    # May have found a modifier
                    modifiers = set(tok.string.upper())
                    if modifiers.difference(MODIFIERS):
                        # Invalid modifier
                        yield from self.reset()
                        continue

                    # Found modifier
                    if Modifier.GLOBAL.value in modifiers:
                        self.is_global = True
                        modifiers.remove(Modifier.GLOBAL.value)
                    self.flags = [Modifier(modifier) for modifier in modifiers]
                    self.collecting_modifiers = CollectState.COMPLETE

                    # Loop round so we can handle the next token more gracefully
                    continue

                else:
                    # Not a modifier
                    self.collecting_modifiers = CollectState.COMPLETE
                    # Fall through to handle this token after rendering regex

            if self.collecting_modifiers == CollectState.COMPLETE:
                # Render regex
                yield self.render()

                # Render this token too - it's not something we're holding
                yield tok.original

                # Clear the state ready for the next regex we find
                self.clear()
                continue

            # Should not get here
            raise ParseError(
                "Parser reached invalid state: match={} replace={} modifiers={}".format(
                    self.collecting_match,
                    self.collecting_replace,
                    self.collecting_modifiers,
                )
            )

        # We've reached the end
        if self.collecting_modifiers != CollectState.WAITING:
            # We've got a completed regex in the state
            yield self.render()
            self.clear()
        else:
            # In case we started collecting one, clear any buffer
            yield from self.reset()

    def render(self):
        """
        Render the regular expression
        """
        # Collect leading whitespace
        variable = self.variable.lstrip()
        whitespace = self.variable[: -len(variable)]
        match = "".join(self.match)

        # Build flags string
        if self.flags:
            flags_ops = " | ".join([f"re.{flag.value}" for flag in self.flags])
            flags = f", flags={flags_ops}"
        else:
            flags = ""

        # Build ops
        if self.op == Op.MATCH:
            # Pass the match into our code so we can set vars
            python = [
                f"{whitespace}__perl__re_match(",
                f"re.{'finditer' if self.is_global else 'search'}",
                f"(r'{match}', {variable}{flags})",
                ")",
            ]

        else:
            replace = "".join(self.replace)
            if self.is_global:
                # By default the count is unlimited
                count = ""
            else:
                # Not global, specify one
                count = ", count=1"

            # Regex needs to reset the vars first in case it's a None
            python = [
                f"{whitespace}{variable} = __perl__reset_vars() or ",
                f"re.sub(r'{match}', '{replace}', {variable}",
                f"{count}{flags})",
            ]

        return "".join(python)

    def translate_fstring(self, fstring):
        translated = []
        ptr = 0
        while True:
            # TODO: deal with escapes
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

        translated.append(fstring[ptr:])
        return "".join(translated)


def translate(src_generator):
    dest_generator = PerlTranslator().translate(src_generator)
    return "".join(dest_generator)


def translate_string(source):
    source_stream = io.StringIO(source).readline
    translated = translate(source_stream)
    return translated
