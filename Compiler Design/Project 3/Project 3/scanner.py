# scanner.py
from typing import List, Optional, Dict
from token_definitions import Token, TokenType


class Scanner:
    """
    Assignment-specific scanner:
      - Keywords: double int long char bool fun if then else true false orelse andalso
      - Operators: = += -= *= /= + - * / // > < == != !
      - Literals: INTLIT (decimal w/ underscores + optional L/l, no leading zero unless 0),
                  DOUBLELIT (digits.digits or .digits; invalid: 1., 00.2),
                  CHARLIT ("a")
      - Separators: ; , ( ) { }
      - Comments: (* ... *)   (not a token, skipped; non-nested)
      - Longest match for operators (+=, //, etc.)
    """

    # Operator tables
    SINGLE_CHAR_TOKENS: Dict[str, str] = {
        "(": "LPAREN", ")": "RPAREN",
        "{": "LBRACE", "}": "RBRACE",
        "[": "LBRACKET", "]": "RBRACKET",
        ",": "COMMA", ".": "DOT",
        ";": "SEMICOLON", ":": "COLON",
        "+": "PLUS", "-": "MINUS",
        "*": "MULTIPLY", "/": "DIVIDE", "%": "MODULO",
        "=": "ASSIGN", ">": "GREATER", "<": "LESS",
        "!": "NOT",
    }

    TWO_CHAR_TOKENS: Dict[str, str] = {
        "==": "EQUALS",
        "!=": "NOTEQUALS",
        ">=": "GREATEREQUAL",
        "<=": "LESSEQUAL",
        "+=": "PLUSASSIGN",
        "-=": "MINUSASSIGN",
        "*=": "MULTIPLYASSIGN",
        "/=": "DIVIDEASSIGN",
        "//": "INTDIV",   # integer division operator
        "**": "POWER",
    }

    KEYWORDS: Dict[str, str] = {
        # assignment language keywords
        "double": "DOUBLE",
        "int": "INT",
        "long": "LONG",
        "char": "CHAR",
        "bool": "BOOL",
        "fun": "FUN",
        "if": "IF",
        "then": "THEN",
        "else": "ELSE",
        "true": "TRUE",
        "false": "FALSE",
        "orelse": "ORELSE",
        "andalso": "ANDALSO",

        # extra general-purpose keywords (not all used by parser)
        "while": "WHILE",
        "for": "FOR",
        "def": "DEF",
        "class": "CLASS",
        "return": "RETURN",
        "import": "IMPORT",
        "from": "FROM",
        "as": "AS",
        "try": "TRY",
        "except": "EXCEPT",
        "finally": "FINALLY",
        "raise": "RAISE",
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_line = 1
        self.start_column = 1

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def scan_tokens(self) -> List[Token]:
        """
        Main method to scan the source code and produce tokens.
        Returns a list of tokens (including a final EOF).
        """
        while not self.is_at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_column = self.column
            self.scan_token()

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def scan_token(self) -> None:
        """
        Scan a single token – core lexing logic.
        """
        c = self.advance()

        # Whitespace / newline
        if c in (" ", "\t", "\r"):
            return
        if c == "\n":
            self._newline()
            return

        # ML-style comments: (* ... *)  (non-nested by spec)
        if c == "(" and self.peek() == "*":
            self.advance()  # consume '*'
            self._consume_ml_comment()
            return

        # Longest-match for two-char operators
        pair = c + self.peek()
        if pair in self.TWO_CHAR_TOKENS:
            self.match(self.peek())
            self._add_token(self.TWO_CHAR_TOKENS[pair])
            return

        # Char literal: exactly 'x'
        if c == "'" and self.peek() != "'" and self.peek_next() == "'":
            ch = self.advance()  # the single char
            self.advance()       # closing '
            self._add_token("CHARLIT", f"'{ch}'")
            return

        # Anything else in single quotes -> INVALID (no multi-char strings, no empty '')
        if c == "'":
            # consume until closing quote or newline/EOF
            while not self.is_at_end() and self.peek() != "'" and self.peek() != "\n":
                self.advance()
            if not self.is_at_end() and self.peek() == "'":
                self.advance()  # closing '
                self._add_token("INVALID", self._lexeme())
            else:
                # unterminated char literal
                self._add_token("INVALID", self._lexeme())
            return

        # Char literal: exactly "x"
        if c == '"' and self.peek() != '"' and self.peek_next() == '"':
            ch = self.advance()  # the single char
            self.advance()       # closing "
            self._add_token("CHARLIT", f'"{ch}"')
            return

        # Anything else in quotes -> INVALID (spec doesn't define multi-char strings)
        if c == '"':
            # consume until closing quote or newline/EOF
            while not self.is_at_end() and self.peek() != '"' and self.peek() != "\n":
                self.advance()
            if not self.is_at_end() and self.peek() == '"':
                self.advance()  # closing "
                self._add_token("INVALID", self._lexeme())
            else:
                # unterminated string
                self._add_token("INVALID", self._lexeme())
            return

        # Numbers: starting with digit
        if self._is_digit(c):
            self._number_starting_with_digit()
            return

        # Numbers: leading dot form .digits
        if c == "." and self._is_digit(self.peek()):
            # keep DOT as part of the number
            self._number_starting_with_dot()
            return

        # Identifiers / keywords: start with letter or underscore
        if self._is_alpha(c) or c == "_":
            self._identifier()
            return

        # Single-char tokens (operators, separators)
        if c in self.SINGLE_CHAR_TOKENS:
            self._add_token(self.SINGLE_CHAR_TOKENS[c])
            return

        # Unknown char -> INVALID
        self._add_token("INVALID", self._lexeme())

    # ------------------------------------------------------------------ #
    # Char stream helpers
    # ------------------------------------------------------------------ #

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

    def peek(self) -> str:
        if self.is_at_end():
            return "\0"
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _newline(self):
        self.line += 1
        self.column = 1

    # ------------------------------------------------------------------ #
    # Token creation helpers
    # ------------------------------------------------------------------ #

    def _lexeme(self) -> str:
        return self.source[self.start:self.current]

    def _add_token(self, token_type_name: str, lexeme: Optional[str] = None):
        ttype = getattr(TokenType, token_type_name)
        lx = self._lexeme() if lexeme is None else lexeme
        self.tokens.append(Token(ttype, lx, self.start_line, self.start_column))

    # ------------------------------------------------------------------ #
    # Recognizers: identifiers, numbers, comments
    # ------------------------------------------------------------------ #

    def _identifier(self):
        while self._is_alnum(self.peek()) or self.peek() == "_":
            self.advance()
        text = self._lexeme()
        ttype_name = self.KEYWORDS.get(text, "IDENTIFIER")
        self._add_token(ttype_name)

    def _number_starting_with_digit(self):
        # integer part
        while self._is_digit(self.peek()):
            self.advance()

        # fractional part?
        if self.peek() == "." and self._is_digit(self.peek_next()):
            # This is a double literal
            self.advance()  # consume '.'
            while self._is_digit(self.peek()):
                self.advance()
            self._add_token("DOUBLELIT")
        else:
            # Just an integer literal
            self._add_token("INTLIT")

    def _number_starting_with_dot(self):
        # We saw '.' and next was digit => .digits form
        while self._is_digit(self.peek()):
            self.advance()
        self._add_token("DOUBLELIT")

    def _consume_ml_comment(self):
        """
        Consume non-nested ML comment: (* ... *)
        Newlines update line/column. Emits INVALID if unterminated.
        """
        while not self.is_at_end():
            if self.peek() == "\n":
                self._newline()
                self.advance()
                continue
            if self.peek() == "*" and self.peek_next() == ")":
                # consume "*)"
                self.advance()
                self.advance()
                return
            self.advance()
        # Unterminated comment – mark as INVALID token
        # (We create an INVALID token for the '(*' we started at)
        self.tokens.append(
            Token(TokenType.INVALID, "Unterminated comment", self.start_line, self.start_column)
        )

    # ------------------------------------------------------------------ #
    # Char classes
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_digit(c: str) -> bool:
        return "0" <= c <= "9"

    @staticmethod
    def _is_alpha(c: str) -> bool:
        return ("a" <= c <= "z") or ("A" <= c <= "Z")

    @classmethod
    def _is_alnum(cls, c: str) -> bool:
        return cls._is_alpha(c) or cls._is_digit(c)
