"""
Token chain object
"""
from __future__ import annotations

import io
import tokenize
from typing import List, Optional, Tuple, cast

from .chain import Item


class Token(Item):
    rendered: Optional[str]

    def __init__(self, tok):
        super().__init__()

        (self.type, self.string, start, end, self.line) = tok
        (self.start_line, self.start_col) = start
        (self.end_line, self.end_col) = end

    def __repr__(self):
        return f"<Token {tokenize.tok_name[self.type]}: {self.string}>"

    @classmethod
    def from_stream(cls, stream) -> Token:
        token_generator = tokenize.generate_tokens(stream)
        start_token = cls.from_iterator(token_generator)
        return start_token

    @classmethod
    def from_string(cls, value: str, rstrip=False) -> Token:
        """
        Generate a token chain from a string
        """
        readline = io.StringIO(value).readline
        start_token = cls.from_stream(readline)
        return start_token

    def rstrip(self) -> Token:
        """
        Strip all NEWLINE, DEDENT and ENDMARKER tokens from the end of this chain

        Returns self
        """
        last_token = self.last
        while last_token.type in [
            tokenize.ENDMARKER,
            tokenize.DEDENT,
            tokenize.ENDMARKER,
        ]:
            last_token = last_token.prev
            if last_token == self:
                # Stop if we have reached ourselves - don't want to detach
                break
            last_token.next = None
        return self

    def _from_iterator_complete(self):
        for tok in self:
            tok.rendered = tok._render()

    def _render(self):
        """
        The standard tokenize.untokzenise does not preserve whitespace, so this uses
        the full token to find the whitespace around the token string
        """
        # Extract start and end and prepare line for value extraction
        lines = self.line.splitlines(keepends=True)

        # Adjust line numbers
        # Line numbers are 1-indexed, but ``lines`` is 0-indexed
        # ``tok.line`` starts at start_line
        end_line = self.end_line - self.start_line
        start_line = 0

        # Skip empty
        if not lines or (start_line == end_line and self.start_col == self.end_col):
            return self.string

        # Use the absolute line numbers
        buffer = []
        if self.prev:
            prev_end_col = self.prev.end_col
            if self.prev.end_line != self.start_line:
                # We're on a new line
                prev_end_col = 0
            if prev_end_col < self.start_col:
                # Found missing whitespace, collect
                buffer.append(lines[0][prev_end_col : self.start_col])

        # Extract token
        if self.start_line == self.end_line:
            # Single line handles differently
            buffer.append(lines[start_line][self.start_col : self.end_col])
        else:
            # Multiple lines
            buffer.append(lines[start_line][self.start_col :])
            for line_num in range(start_line + 1, end_line):
                buffer.append(lines[line_num])
            buffer.append(lines[end_line][: self.end_col])

        return "".join(buffer)

    def get_to_slash(self) -> Tuple[Optional[Token], List[Token]]:
        """
        Find all content up to the next ``/``

        Return the ``/`` token and a list of the tokens before it
        """
        found: List[Token] = []
        tok: Optional[Token] = self
        escapes: int = 0

        while tok:
            # Check if this is an escape
            if tok.type == tokenize.OP and tok.string == "/":
                if escapes % 2:
                    # Uneven number of escapes before this token - actual escape
                    # Last character was escaping this slash
                    found.pop()
                else:
                    # This is the slash we were looking for
                    break

            elif tok.type == tokenize.ERRORTOKEN and tok.string == "\\":
                escapes += 1

            else:
                escapes = 0

            # Store this token and advance
            found.append(tok)
            tok = cast(Token, tok.next)

        return tok, found

    def translate(self, value: str, end: Token) -> Token:
        # end_next: Optional[Token] = cast(Optional[Token], end.next)
        # if end_next:
        #    whitespace = end_next.render()[: -len(end_next.string)]

        replacement = Token.from_string(value).rstrip()

        # Copy the end col across from the current end to the new end to allow
        # render() to correctly detect where it should start rendering from
        # replacement_last = replacement.last
        # replacement_last.end_col = end.end_col
        # replacement_last.end_line = end.end_line

        # replacement.last.whitespace = whitespace
        self.replace(chain=replacement, end=end)
        return replacement
