
import re
from typing import Optional, Pattern

from token_definitions import Token, TokenType, Position
from scanner import Scanner


class PatternMatcher:
    """Utility class for ad-hoc pattern matching on substrings.

    This is **not** used by the main Scanner in scanner.py yet, but it can be
    helpful for unit tests or for experimenting with alternative tokenization
    strategies (e.g., quickly checking how an identifier or number would be
    classified).
    """

    def __init__(self) -> None:
        # Compile regex patterns for different token types
        # All patterns are anchored at the start of the string.
        self.identifier_pattern: Pattern[str] = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*')
        # very simple number pattern: digits or digits.digits
        self.number_pattern: Pattern[str] = re.compile(r'^[0-9]+(\.[0-9]+)?')
        # double-quoted string without newlines or escapes
        self.string_pattern: Pattern[str] = re.compile(r'^"[^"\n]*"')
        # ML comment pattern: (* ... *)
        self.ml_comment_pattern: Pattern[str] = re.compile(r'^\(\*.*?\*\)', re.DOTALL)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def match_pattern(self, text: str, line: int, column: int) -> Optional[Token]:
        """Match *one* token at the beginning of ``text``.

        Returns a Token if a token can be recognized, otherwise ``None``.
        The caller is responsible for advancing by the matched lexeme's length.
        """
        if not text:
            return None

        # Comments first
        tok = self.handle_comment(text, line, column)
        if tok is not None:
            return tok

        # String literal
        m = self.string_pattern.match(text)
        if m:
            lexeme = m.group(0)
            return self._make_token(TokenType.STRING, lexeme, line, column)

        # Identifier or keyword
        m = self.identifier_pattern.match(text)
        if m:
            lexeme = m.group(0)
            # Re-use Scanner.KEYWORDS table so classification stays consistent
            tt_name = Scanner.KEYWORDS.get(lexeme)
            if tt_name is not None and hasattr(TokenType, tt_name):
                ttype = getattr(TokenType, tt_name)
            else:
                ttype = TokenType.IDENTIFIER
            return self._make_token(ttype, lexeme, line, column)

        # Number (INTLIT or DOUBLELIT – simplified rule)
        m = self.number_pattern.match(text)
        if m:
            lexeme = m.group(0)
            if "." in lexeme:
                ttype = TokenType.DOUBLELIT
            else:
                ttype = TokenType.INTLIT
            return self._make_token(ttype, lexeme, line, column)

        # Nothing matched: treat as lexical error
        return self.handle_errors(text, line, column)

    # ------------------------------------------------------------------ #
    # Helpers / special handlers
    # ------------------------------------------------------------------ #

    def handle_string_literal(self, text: str, line: int, column: int) -> Optional[Token]:
        """Handle a double-quoted string literal.

        If the closing quote is missing on the same line, we return an INVALID token.
        """
        m = self.string_pattern.match(text)
        if m:
            lexeme = m.group(0)
            return self._make_token(TokenType.STRING, lexeme, line, column)

        # Unterminated string (no closing quote on this line)
        if text.startswith('"'):
            end = text.find("\n")
            if end == -1:
                end = len(text)
            lexeme = text[:end]
            return self._make_token(TokenType.INVALID, lexeme, line, column)

        return None

    def handle_comment(self, text: str, line: int, column: int) -> Optional[Token]:
        """Handle ML-style comments of the form (* ... *).

        The main scanner *skips* comments and does not emit COMMENT tokens.
        Here we return a COMMENT token mainly so you can unit-test this component
        if you choose to use it.
        """
        if text.startswith("(*"):
            m = self.ml_comment_pattern.match(text)
            if m:
                lexeme = m.group(0)
                return self._make_token(TokenType.COMMENT, lexeme, line, column)
            # Unterminated comment
            lexeme = text
            return self._make_token(TokenType.INVALID, lexeme, line, column)
        return None

    def handle_errors(self, text: str, line: int, column: int) -> Optional[Token]:
        """Fallback error handler.

        When no known pattern matches, we mark the first non-whitespace character
        as INVALID. This mirrors the behaviour of the main Scanner.
        """
        # Skip leading whitespace when reporting error span
        i = 0
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return None

        # Take either the single character or up to next whitespace as error lexeme
        j = i + 1
        while j < len(text) and not text[j].isspace():
            j += 1

        lexeme = text[i:j]
        return self._make_token(TokenType.INVALID, lexeme, line, column + i)

    # ------------------------------------------------------------------ #

    def _make_token(self, ttype: TokenType, lexeme: str, line: int, column: int) -> Token:
        # We construct a minimal Position; index/filename are left at defaults.
        pos = Position(line=line, column=column, index=0, filename=None)
        return Token(ttype, lexeme, line, column, pos)
