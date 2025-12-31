# parser.py
from typing import List
from token_definitions import Token, TokenType
from scanner import Scanner


class ParseError(Exception):
    """Syntactic error raised by the parser."""
    pass


class Parser:
    """
    Chapter 3-style recursive-descent LL(1) parser.

    Grammar (refactored to handle arithmetic + boolean expressions cleanly):

      Program      → StmtList EOF
      StmtList     → Stmt StmtList | ε

      Stmt         → DeclareStmt
                   | AssignStmt
                   | FunctionDefStmt
                   | FunctionCallStmt
                   | Block

      Block        → '{' StmtList '}'

      DeclareStmt  → Type IdList ';'
      Type         → int | double | bool | char | long
      IdList       → IDENTIFIER (',' IDENTIFIER)*

      AssignStmt   → IDENTIFIER AssignOp Expression ';'
      AssignOp     → '=' | '+=' | '-=' | '*=' | '/='

      FunctionDefStmt → fun IDENTIFIER '(' ParamList? ')' '=' Expression ';'
      ParamList       → Type IDENTIFIER (',' Type IDENTIFIER)*

      FunctionCallStmt → FunctionCall ';'
      FunctionCall     → IDENTIFIER '(' ArgList? ')'
      ArgList          → Expression (',' Expression)*

      Expression   → IfExpr
                   | LogicOrExpr

      IfExpr       → if LogicOrExpr then Expression else Expression

      LogicOrExpr  → LogicAndExpr ('orelse' LogicAndExpr)*
      LogicAndExpr → RelExpr ('andalso' RelExpr)*
      RelExpr      → ArithExpr (CompOp ArithExpr)?
      CompOp       → '==' | '>' | '<'

      ArithExpr    → Term (('+' | '-') Term)*
      Term         → Value (('*' | '/' | '//') Factor)*
      Value        → Factor | '-' Factor

      Factor       → '(' Expression ')'
                   | FunctionCall
                   | IDENTIFIER
                   | INTLIT
                   | CHARLIT
                   | DOUBLELIT
                   | true
                   | false
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.productions: List[str] = []

    # ---------- Public entrypoint ----------

    def parse(self) -> List[str]:
        """Parse a full program and return the list of productions used."""
        self.productions.clear()
        self._program()
        self._consume(TokenType.EOF, "Expected end of input.")
        return self.productions

    # ---------- Grammar: Program & StmtList ----------

    def _program(self) -> None:
        self._record("Program -> StmtList EOF")
        self._stmt_list()

    def _stmt_list(self) -> None:
        """
        StmtList -> Stmt StmtList | ε
        """
        while self._can_start_stmt(self._peek().type):
            self._record("StmtList -> Stmt StmtList")
            self._statement()
        self._record("StmtList -> ε")  # epsilon

    def _can_start_stmt(self, ttype: TokenType) -> bool:
        return ttype in {
            TokenType.INT,
            TokenType.DOUBLE,
            TokenType.BOOL,
            TokenType.CHAR,
            TokenType.LONG,
            TokenType.FUN,
            TokenType.IDENTIFIER,
            TokenType.LBRACE,
        }

    # ---------- Statements ----------

    def _statement(self) -> None:
        """
        Stmt -> DeclareStmt
              | AssignStmt
              | FunctionDefStmt
              | FunctionCallStmt
              | Block
        """
        tok = self._peek()

        if tok.type == TokenType.LBRACE:
            self._record("Stmt -> Block")
            self._block()
            return

        if tok.type in {
            TokenType.INT,
            TokenType.DOUBLE,
            TokenType.BOOL,
            TokenType.CHAR,
            TokenType.LONG,
        }:
            self._record("Stmt -> DeclareStmt")
            self._declare_stmt()
            return

        if tok.type == TokenType.FUN:
            self._record("Stmt -> FunctionDefStmt")
            self._function_def_stmt()
            return

        if tok.type == TokenType.IDENTIFIER:
            # lookahead for '(' => function call
            if self._peek_next().type == TokenType.LPAREN:
                self._record("Stmt -> FunctionCallStmt")
                self._function_call_stmt()
            else:
                self._record("Stmt -> AssignStmt")
                self._assign_stmt()
            return

        raise self._error(tok, "Unexpected token at start of statement.")

    def _block(self) -> None:
        """Block → '{' StmtList '}'"""
        self._record("Block -> '{' StmtList '}'")
        self._consume(TokenType.LBRACE, "Expected '{' to start block.")
        self._stmt_list()
        self._consume(TokenType.RBRACE, "Expected '}' to end block.")

    # ---------- Declarations ----------

    def _declare_stmt(self) -> None:
        """DeclareStmt → Type IdList ';'"""
        self._record("DeclareStmt -> Type IdList ';'")
        self._type_keyword()
        self._id_list()
        self._consume(TokenType.SEMICOLON, "Expected ';' after declaration.")

    def _type_keyword(self) -> None:
        """Type → int | double | bool | char | long"""
        self._record("Type -> (int|double|bool|char|long)")
        if not self._match(
            TokenType.INT,
            TokenType.DOUBLE,
            TokenType.BOOL,
            TokenType.CHAR,
            TokenType.LONG,
        ):
            raise self._error(
                self._peek(), "Expected type keyword (int, double, bool, char, long)."
            )

    def _id_list(self) -> None:
        """IdList → IDENTIFIER (',' IDENTIFIER)*"""
        self._record("IdList -> IDENTIFIER (',' IDENTIFIER)*")
        self._consume(TokenType.IDENTIFIER, "Expected identifier.")
        while self._match(TokenType.COMMA):
            self._consume(TokenType.IDENTIFIER, "Expected identifier after ','.")

    # ---------- Assignment ----------

    def _assign_stmt(self) -> None:
        """AssignStmt → IDENTIFIER AssignOp Expression ';'"""
        self._record("AssignStmt -> IDENTIFIER AssignOp Expression ';'")
        self._consume(TokenType.IDENTIFIER, "Expected identifier at start of assignment.")

        if not self._match(
            TokenType.ASSIGN,
            TokenType.PLUSASSIGN,
            TokenType.MINUSASSIGN,
            TokenType.MULTIPLYASSIGN,
            TokenType.DIVIDEASSIGN,
        ):
            raise self._error(
                self._peek(), "Expected assignment operator (=, +=, -=, *=, /=)."
            )

        self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after assignment.")

    # ---------- Functions ----------

    def _function_def_stmt(self) -> None:
        """FunctionDefStmt → fun IDENTIFIER '(' ParamList? ')' '=' Expression ';'"""
        self._record("FunctionDefStmt -> fun IDENTIFIER '(' ParamList? ')' '=' Expression ';'")
        self._consume(TokenType.FUN, "Expected 'fun'.")
        self._consume(TokenType.IDENTIFIER, "Expected function name after 'fun'.")
        self._consume(TokenType.LPAREN, "Expected '(' after function name.")

        if not self._check(TokenType.RPAREN):
            self._param_list()

        self._consume(TokenType.RPAREN, "Expected ')' after parameter list.")
        self._consume(TokenType.ASSIGN, "Expected '=' before function body.")
        self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after function definition.")

    def _param_list(self) -> None:
        """ParamList → Type IDENTIFIER (',' Type IDENTIFIER)*"""
        self._record("ParamList -> Type IDENTIFIER (',' Type IDENTIFIER)*")
        self._type_keyword()
        self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
        while self._match(TokenType.COMMA):
            self._type_keyword()
            self._consume(TokenType.IDENTIFIER, "Expected parameter name.")

    def _function_call_stmt(self) -> None:
        """FunctionCallStmt → FunctionCall ';'"""
        self._record("FunctionCallStmt -> FunctionCall ';'")
        self._function_call()
        self._consume(TokenType.SEMICOLON, "Expected ';' after function call.")

    def _function_call(self) -> None:
        """FunctionCall → IDENTIFIER '(' ArgList? ')'"""
        self._record("FunctionCall -> IDENTIFIER '(' ArgList? ')'")
        self._consume(TokenType.IDENTIFIER, "Expected function name.")
        self._consume(TokenType.LPAREN, "Expected '(' after function name.")

        if not self._check(TokenType.RPAREN):
            self._arg_list()

        self._consume(TokenType.RPAREN, "Expected ')' after argument list.")

    def _arg_list(self) -> None:
        """ArgList → Expression (',' Expression)*"""
        self._record("ArgList -> Expression (',' Expression)*")
        self._expression()
        while self._match(TokenType.COMMA):
            self._expression()

    # ---------- Expressions (top level) ----------

    def _expression(self) -> None:
        """Expression → IfExpr | LogicOrExpr"""
        if self._check(TokenType.IF):
            self._record("Expression -> IfExpr")
            self._if_expr()
        else:
            self._record("Expression -> LogicOrExpr")
            self._logic_or_expr()

    def _if_expr(self) -> None:
        """IfExpr → if LogicOrExpr then Expression else Expression"""
        self._record("IfExpr -> if LogicOrExpr then Expression else Expression")
        self._consume(TokenType.IF, "Expected 'if'.")
        self._logic_or_expr()
        self._consume(TokenType.THEN, "Expected 'then' after condition.")
        self._expression()
        self._consume(TokenType.ELSE, "Expected 'else' after then-branch.")
        self._expression()

    # ---------- Boolean + comparison structure ----------

    def _logic_or_expr(self) -> None:
        """LogicOrExpr → LogicAndExpr ('orelse' LogicAndExpr)*"""
        self._record("LogicOrExpr -> LogicAndExpr ('orelse' LogicAndExpr)*")
        self._logic_and_expr()
        while self._match(TokenType.ORELSE):
            self._logic_and_expr()

    def _logic_and_expr(self) -> None:
        """LogicAndExpr → RelExpr ('andalso' RelExpr)*"""
        self._record("LogicAndExpr -> RelExpr ('andalso' RelExpr)*")
        self._rel_expr()
        while self._match(TokenType.ANDALSO):
            self._rel_expr()

    def _rel_expr(self) -> None:
        """RelExpr → ArithExpr (CompOp ArithExpr)?"""
        self._record("RelExpr -> ArithExpr (CompOp ArithExpr)?")
        self._arith_expr()
        if self._match(TokenType.EQUALS, TokenType.GREATER, TokenType.LESS):
            self._record("RelExpr -> ... CompOp ArithExpr")
            self._arith_expr()

    # ---------- Arithmetic ----------

    def _arith_expr(self) -> None:
        """ArithExpr → Term (('+' | '-') Term)*"""
        self._record("ArithExpr -> Term (('+' | '-') Term)*")
        self._term()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            self._term()

    def _term(self) -> None:
        """Term → Value (('*' | '/' | '//') Factor)*"""
        self._record("Term -> Value (('*' | '/' | '//') Factor)*")
        self._value()
        while self._match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.INTDIV):
            self._factor()

    def _value(self) -> None:
        """Value → Factor | '-' Factor"""
        if self._match(TokenType.MINUS):
            self._record("Value -> '-' Factor")
            self._factor()
        else:
            self._record("Value -> Factor")
            self._factor()

    def _factor(self) -> None:
        """
        Factor → '(' Expression ')'
               | FunctionCall
               | IDENTIFIER
               | INTLIT
               | CHARLIT
               | DOUBLELIT
               | true
               | false
        """
        if self._match(TokenType.LPAREN):
            self._record("Factor -> '(' Expression ')'")
            self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return

        # identifier or function call
        if self._check(TokenType.IDENTIFIER):
            if self._peek_next().type == TokenType.LPAREN:
                self._record("Factor -> FunctionCall")
                self._function_call()
            else:
                self._record("Factor -> IDENTIFIER")
                self._advance()
            return

        # literals: int, char, double, bool
        if self._match(
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.INTLIT,
            TokenType.CHARLIT,
            TokenType.DOUBLELIT,
        ):
            self._record("Factor -> literal")
            return

        raise self._error(self._peek(), "Expected expression factor.")

    # ---------- Low-level helpers ----------

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, ttype: TokenType, message: str) -> Token:
        if self._check(ttype):
            return self._advance()
        raise self._error(self._peek(), message)

    def _check(self, ttype: TokenType) -> bool:
        if self.current >= len(self.tokens):
            return False
        return self._peek().type == ttype

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _peek_next(self) -> Token:
        if self.current + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.current + 1]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, token: Token, message: str) -> ParseError:
        location = f"line {token.line}, column {token.column}"
        val = getattr(token, "value", "")
        return ParseError(
            f"{location}: {message} (found {val!r}, type={token.type})"
        )

    def _record(self, production: str) -> None:
        """Record which production rule was used (for documentation / debugging)."""
        self.productions.append(production)


# Convenience function for tests
def parse_source(source: str) -> List[str]:
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    return parser.parse()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python parser.py <source-file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        src = f.read()

    try:
        productions = parse_source(src)
        print("Parse succeeded.")
        print("Productions used:")
        for p in productions:
            print("  ", p)
    except ParseError as e:
        print("Parse error:", e)
