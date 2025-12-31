# Assigned to: Parikshith
# Responsibility: Token Definition and Management

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class TokenType(Enum):
    # Language Keywords (assignment spec) 
    IF = "IF"
    ELSE = "ELSE"
    WHILE = "WHILE"
    FOR = "FOR"
    DEF = "DEF"
    CLASS = "CLASS"
    RETURN = "RETURN"
    IMPORT = "IMPORT"
    FROM = "FROM"
    AS = "AS"
    TRY = "TRY"
    EXCEPT = "EXCEPT"
    FINALLY = "FINALLY"
    RAISE = "RAISE"

    DOUBLE = "DOUBLE"
    INT = "INT"
    LONG = "LONG"
    CHAR = "CHAR"
    BOOL = "BOOL"
    FUN = "FUN"
    THEN = "THEN"
    TRUE = "TRUE"
    FALSE = "FALSE"
    ORELSE = "ORELSE"
    ANDALSO = "ANDALSO"
    

    # Operators
    PLUS = "PLUS"                  # +
    MINUS = "MINUS"                # -
    MULTIPLY = "MULTIPLY"          # *
    DIVIDE = "DIVIDE"              # /
    MODULO = "MODULO"              # %
    POWER = "POWER"                # **
    ASSIGN = "ASSIGN"              # =
    PLUSASSIGN = "PLUSASSIGN"      # +=
    MINUSASSIGN = "MINUSASSIGN"    # -=
    EQUALS = "EQUALS"              # ==
    NOTEQUALS = "NOTEQUALS"        # !=
    GREATER = "GREATER"            # >
    LESS = "LESS"                  # <
    GREATEREQUAL = "GREATEREQUAL"  # >=
    LESSEQUAL = "LESSEQUAL"        # <=

    NOT = "NOT"                    # !
    INTDIV = "INTDIV"              # //  (integer division)
    MULTIPLYASSIGN = "MULTIPLYASSIGN"  # *=
    DIVIDEASSIGN = "DIVIDEASSIGN"      # /=

    # Delimiters
    LPAREN = "LPAREN"              # (
    RPAREN = "RPAREN"              # )
    LBRACE = "LBRACE"              # {
    RBRACE = "RBRACE"              # }
    LBRACKET = "LBRACKET"          # [
    RBRACKET = "RBRACKET"          # ]
    COMMA = "COMMA"                # ,
    DOT = "DOT"                    # .
    COLON = "COLON"                # :
    SEMICOLON = "SEMICOLON"        # ;

    # Identifiers & Literals
    IDENTIFIER = "IDENTIFIER" # Variable names, function names, etc.
    NUMBER = "NUMBER"         # Integers and floating-point numbers
    STRING = "STRING"         # String literals

    INTLIT = "INTLIT"
    DOUBLELIT = "DOUBLELIT"
    CHARLIT = "CHARLIT"

    # Comments / whitespace
    COMMENT = "COMMENT"
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"

    # Error handling
    INVALID = "INVALID"

    # End of File
    EOF = "EOF"

class Position:
    """Tracks position in source code, including file, line, and column information."""
    def __init__(self, line: int, column: int, index: int = 0, filename: str = "<unknown>"):
        self.line = line
        self.column = column
        self.index = index
        self.filename = filename

    def advance(self, current_char: str = "") -> 'Position':
        self.index += 1
        self.column += 1

        if current_char == '\n':
            self.line += 1
            self.column = 0

        return self

    def copy(self) -> 'Position':
        return Position(self.line, self.column, self.index, self.filename)

    def __str__(self) -> str:
        return f"line {self.line}, column {self.column}"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    position: Optional[Position] = None

    @property
    def is_keyword(self) -> bool:
        return self.type in {
            TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.FOR,
            TokenType.DEF, TokenType.CLASS, TokenType.RETURN, TokenType.IMPORT,
            TokenType.FROM, TokenType.AS, TokenType.TRY, TokenType.EXCEPT,
            TokenType.FINALLY, TokenType.RAISE,
            TokenType.DOUBLE, TokenType.INT, TokenType.LONG, TokenType.CHAR,
            TokenType.BOOL, TokenType.FUN, TokenType.THEN, TokenType.TRUE,
            TokenType.FALSE, TokenType.ORELSE, TokenType.ANDALSO
        }

    @property
    def is_operator(self) -> bool:
        return self.type in {
            TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE,
            TokenType.MODULO, TokenType.POWER, TokenType.ASSIGN, TokenType.PLUSASSIGN,
            TokenType.MINUSASSIGN, TokenType.EQUALS, TokenType.NOTEQUALS,
            TokenType.GREATER, TokenType.LESS, TokenType.GREATEREQUAL,
            TokenType.LESSEQUAL, TokenType.NOT, TokenType.INTDIV,
            TokenType.MULTIPLYASSIGN, TokenType.DIVIDEASSIGN
        }

    @property
    def is_delimiter(self) -> bool:
        return self.type in {
            TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE, TokenType.RBRACE,
            TokenType.LBRACKET, TokenType.RBRACKET, TokenType.COMMA, TokenType.DOT,
            TokenType.COLON, TokenType.SEMICOLON
        }

    def matches(self, token_type: TokenType, value: Optional[str] = None) -> bool:
        return self.type == token_type and (value is None or self.value == value)

    def validate(self) -> bool:
        """Validate based on type (scanner already handles most rules)."""
        if self.type in {TokenType.INTLIT, TokenType.DOUBLELIT, TokenType.CHARLIT}:
            return True  # validated in scanner
        if self.type == TokenType.IDENTIFIER:
            return self.value.isidentifier()
        if self.type == TokenType.INVALID:
            return False
        return True

    def __str__(self) -> str:
        pos = f" @ {self.position}" if self.position else f" (line {self.line}, col {self.column})"
        return f"Token({self.type.name}, '{self.value}'{pos})"


# ---------- Utility creation helpers ----------
def create_keyword_token(keyword: str, position: Position) -> Token:
    try:
        token_type = TokenType[keyword.upper()]
        return Token(token_type, keyword, position.line, position.column, position)
    except KeyError:
        return Token(TokenType.IDENTIFIER, keyword, position.line, position.column, position)

def create_operator_token(operator: str, position: Position) -> Optional[Token]:
    operator_map = {
        '+': TokenType.PLUS,
        '-': TokenType.MINUS,
        '*': TokenType.MULTIPLY,
        '/': TokenType.DIVIDE,
        '%': TokenType.MODULO,
        '**': TokenType.POWER,
        '=': TokenType.ASSIGN,
        '+=': TokenType.PLUSASSIGN,
        '-=': TokenType.MINUSASSIGN,
        '==': TokenType.EQUALS,
        '!=': TokenType.NOTEQUALS,
        '>': TokenType.GREATER,
        '<': TokenType.LESS,
        '>=': TokenType.GREATEREQUAL,
        '<=': TokenType.LESSEQUAL,
        '!': TokenType.NOT,
        '//': TokenType.INTDIV,
        '*=': TokenType.MULTIPLYASSIGN,
        '/=': TokenType.DIVIDEASSIGN,
    }

    ttype = operator_map.get(operator)
    if ttype is None:
        return None
    return Token(ttype, operator, position.line, position.column, position)


def create_delimiter_token(delimiter: str, position: Position) -> Optional[Token]:
    delimiter_map = {
        '(': TokenType.LPAREN,
        ')': TokenType.RPAREN,
        '{': TokenType.LBRACE,
        '}': TokenType.RBRACE,
        '[': TokenType.LBRACKET,
        ']': TokenType.RBRACKET,
        ',': TokenType.COMMA,
        '.': TokenType.DOT,
        ':': TokenType.COLON,
        ';': TokenType.SEMICOLON,
    }

    ttype = delimiter_map.get(delimiter)
    if ttype is None:
        return None
    return Token(ttype, delimiter, position.line, position.column, position)
