# parser.py
from typing import List, Optional

from token_definitions import Token, TokenType
from scanner import Scanner

from symbol_table import (
    SymbolTable,
    BasicType,
    can_widen,
    widened_type,
)
from ast_nodes import (
    ProgramNode,
    BlockNode,
    StmtNode,
    AssignNode,
    FunctionDefNode,
    FunctionCallStmtNode,
    FunctionCallExpr,
    IfExprNode,
    BinaryOpNode,
    UnaryOpNode,
    IdentifierExpr,
    LiteralExpr,
    ExprNode,
)


class ParseError(Exception):
    """Syntactic / semantic error raised by the parser."""
    pass


class Parser:
    """
    Recursive-descent LL(1) parser (Engineering a Compiler, 3rd Ed – Chapter 3)
    extended with:

      - Symbol table generation (Chapter 4 style)
      - Minimal AST construction
      - Basic type checking with int → long → double widening

    Grammar (same as Project 2, but semantic actions added):

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

        # Production trace (still available for debugging)
        self.productions: List[str] = []

        # Symbol table / scope management
        self.global_scope = SymbolTable(parent=None, scope_name="global")
        self.current_scope = self.global_scope
        self.scopes: List[SymbolTable] = [self.global_scope]

    # ---------- Public entrypoint ----------

    def parse(self) -> ProgramNode:
        """
        Parse a full program, build symbol tables + AST, and
        return the ProgramNode root.
        """
        self.productions.clear()
        program = self._program()
        self._consume(TokenType.EOF, "Expected end of input.")
        return program

    # ---------- Grammar: Program & StmtList ----------

    def _program(self) -> ProgramNode:
        self._record("Program -> StmtList EOF")
        stmts = self._stmt_list()
        return ProgramNode(statements=stmts)

    def _stmt_list(self) -> List[StmtNode]:
        """
        StmtList -> Stmt StmtList | ε

        Returns a flat list of *non-declaration* statement AST nodes.
        Declarations affect the symbol table but are not in the AST.
        """
        result: List[StmtNode] = []
        while self._can_start_stmt(self._peek().type):
            self._record("StmtList -> Stmt StmtList")
            stmt = self._statement()
            if stmt is not None:
                result.append(stmt)
        self._record("StmtList -> ε")
        return result

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

    def _statement(self) -> Optional[StmtNode]:
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
            return self._block()

        if tok.type in {
            TokenType.INT,
            TokenType.DOUBLE,
            TokenType.BOOL,
            TokenType.CHAR,
            TokenType.LONG,
        }:
            self._record("Stmt -> DeclareStmt")
            self._declare_stmt()
            return None  # declarations are NOT in AST

        if tok.type == TokenType.FUN:
            self._record("Stmt -> FunctionDefStmt")
            return self._function_def_stmt()

        if tok.type == TokenType.IDENTIFIER:
            # lookahead for '(' => function call
            if self._peek_next().type == TokenType.LPAREN:
                self._record("Stmt -> FunctionCallStmt")
                return self._function_call_stmt()
            else:
                self._record("Stmt -> AssignStmt")
                return self._assign_stmt()

        raise self._error(tok, "Unexpected token at start of statement.")

    def _block(self) -> BlockNode:
        """Block → '{' StmtList '}' with a new nested scope."""
        self._record("Block -> '{' StmtList '}'")
        self._consume(TokenType.LBRACE, "Expected '{' to start block.")

        # Enter new scope
        new_scope = SymbolTable(parent=self.current_scope, scope_name="block")
        self.current_scope = new_scope
        self.scopes.append(new_scope)

        stmts = self._stmt_list()

        # Exit scope
        self._consume(TokenType.RBRACE, "Expected '}' to end block.")
        self.current_scope = new_scope.parent  # restore parent

        return BlockNode(statements=stmts)

    # ---------- Declarations (symbol table only) ----------

    def _declare_stmt(self) -> None:
        """DeclareStmt → Type IdList ';'"""
        self._record("DeclareStmt -> Type IdList ';'")
        typ = self._type_keyword()
        names = self._id_list()

        size = self._size_of_type(typ)
        for name in names:
            try:
                self.current_scope.declare(name, typ, size)
            except ValueError as e:
                # duplicate declaration in same scope
                raise self._error(self._peek(), str(e))

        self._consume(TokenType.SEMICOLON, "Expected ';' after declaration.")

    def _type_keyword(self) -> BasicType:
        """Type → int | double | bool | char | long"""
        self._record("Type -> (int|double|bool|char|long)")
        tok = self._peek()
        if self._match(TokenType.INT):
            return BasicType.INT
        if self._match(TokenType.DOUBLE):
            return BasicType.DOUBLE
        if self._match(TokenType.LONG):
            return BasicType.LONG
        if self._match(TokenType.BOOL):
            return BasicType.BOOL
        if self._match(TokenType.CHAR):
            return BasicType.CHAR

        raise self._error(
            tok, "Expected type keyword (int, double, bool, char, long)."
        )

    def _id_list(self) -> List[str]:
        """IdList → IDENTIFIER (',' IDENTIFIER)*"""
        self._record("IdList -> IDENTIFIER (',' IDENTIFIER)*")
        names: List[str] = []
        first = self._consume(TokenType.IDENTIFIER, "Expected identifier.")
        names.append(first.value)
        while self._match(TokenType.COMMA):
            nxt = self._consume(TokenType.IDENTIFIER, "Expected identifier after ','.")
            names.append(nxt.value)
        return names

    def _size_of_type(self, typ: BasicType) -> int:
        if typ == BasicType.INT:
            return 4
        if typ == BasicType.LONG:
            return 8
        if typ == BasicType.DOUBLE:
            return 8
        if typ == BasicType.BOOL:
            return 4
        if typ == BasicType.CHAR:
            return 1
        return 4

    # ---------- Assignment ----------

    def _assign_stmt(self) -> AssignNode:
        """AssignStmt → IDENTIFIER AssignOp Expression ';'"""
        self._record("AssignStmt -> IDENTIFIER AssignOp Expression ';'")

        name_tok = self._consume(
            TokenType.IDENTIFIER, "Expected identifier at start of assignment."
        )
        var_name = name_tok.value

        sym = self.current_scope.lookup(var_name)
        if sym is None:
            raise self._error(
                name_tok, f"Use of undeclared variable '{var_name}'."
            )

        op_tok = self._consume_assign_op()
        expr = self._expression()

        # Type check assignment: RHS must be widenable to LHS
        if expr.typ is None:
            raise self._error(name_tok, "Internal error: expression has no type.")
        if not can_widen(expr.typ, sym.type):
            raise self._error(
                name_tok,
                f"Type error in assignment to '{var_name}': cannot assign {expr.typ} to {sym.type}.",
            )

        self._consume(TokenType.SEMICOLON, "Expected ';' after assignment.")
        return AssignNode(name=var_name, op=op_tok.value, expr=expr)

    def _consume_assign_op(self) -> Token:
        if self._match(
            TokenType.ASSIGN,
            TokenType.PLUSASSIGN,
            TokenType.MINUSASSIGN,
            TokenType.MULTIPLYASSIGN,
            TokenType.DIVIDEASSIGN,
        ):
            return self._previous()
        raise self._error(
            self._peek(), "Expected assignment operator (=, +=, -=, *=, /=)."
        )

    # ---------- Functions ----------

    def _function_def_stmt(self) -> FunctionDefNode:
        """FunctionDefStmt → fun IDENTIFIER '(' ParamList? ')' '=' Expression ';'"""
        self._record(
            "FunctionDefStmt -> fun IDENTIFIER '(' ParamList? ')' '=' Expression ';'"
        )
        fun_tok = self._consume(TokenType.FUN, "Expected 'fun'.")
        name_tok = self._consume(
            TokenType.IDENTIFIER, "Expected function name after 'fun'."
        )
        fun_name = name_tok.value

        self._consume(TokenType.LPAREN, "Expected '(' after function name.")

        # Enter new scope for parameters + body
        fun_scope = SymbolTable(parent=self.current_scope, scope_name=f"fun {fun_name}")
        self.current_scope = fun_scope
        self.scopes.append(fun_scope)

        param_types: List[BasicType] = []
        param_names: List[str] = []

        if not self._check(TokenType.RPAREN):
            # ParamList → Type IDENTIFIER (',' Type IDENTIFIER)*
            first_type = self._type_keyword()
            first_name_tok = self._consume(
                TokenType.IDENTIFIER, "Expected parameter name."
            )
            param_types.append(first_type)
            param_names.append(first_name_tok.value)
            self.current_scope.declare(
                first_name_tok.value, first_type, self._size_of_type(first_type)
            )

            while self._match(TokenType.COMMA):
                t = self._type_keyword()
                n_tok = self._consume(
                    TokenType.IDENTIFIER, "Expected parameter name after type."
                )
                param_types.append(t)
                param_names.append(n_tok.value)
                self.current_scope.declare(
                    n_tok.value, t, self._size_of_type(t)
                )

        self._consume(TokenType.RPAREN, "Expected ')' after parameter list.")
        self._consume(TokenType.ASSIGN, "Expected '=' before function body.")

        # Parse body expression inside function scope
        body_expr = self._expression()
        if body_expr.typ is None:
            raise self._error(fun_tok, "Internal error: function body has no type.")

        self._consume(TokenType.SEMICOLON, "Expected ';' after function definition.")

        # Exit function scope
        self.current_scope = fun_scope.parent

        # Declare function in GLOBAL scope with its inferred return type
        try:
            self.global_scope.declare(
                fun_name,
                body_expr.typ,
                self._size_of_type(body_expr.typ),
            )
        except ValueError as e:
            # duplicate function name
            raise self._error(fun_tok, str(e))

        return FunctionDefNode(
            name=fun_name,
            param_names=param_names,
            param_types=param_types,
            body=body_expr,
        )

    def _function_call_stmt(self) -> FunctionCallStmtNode:
        """FunctionCallStmt → FunctionCall ';'"""
        call_expr = self._function_call()
        self._consume(TokenType.SEMICOLON, "Expected ';' after function call.")
        return FunctionCallStmtNode(call=call_expr)

    def _function_call(self) -> FunctionCallExpr:
        """FunctionCall → IDENTIFIER '(' ArgList? ')'"""
        name_tok = self._consume(
            TokenType.IDENTIFIER, "Expected function name in call."
        )
        fun_name = name_tok.value

        fun_sym = self.global_scope.lookup(fun_name)
        if fun_sym is None:
            raise self._error(name_tok, f"Call to undeclared function '{fun_name}'.")

        self._consume(TokenType.LPAREN, "Expected '(' after function name in call.")
        args: List[ExprNode] = []
        if not self._check(TokenType.RPAREN):
            # ArgList → Expression (',' Expression)*
            args.append(self._expression())
            while self._match(TokenType.COMMA):
                args.append(self._expression())
        self._consume(TokenType.RPAREN, "Expected ')' after arguments.")

        call = FunctionCallExpr(name=fun_name, args=args)
        # Return type is the symbol's type (inferred from definition)
        call.typ = fun_sym.type
        return call

    # ---------- Expressions ----------

    def _expression(self) -> ExprNode:
        """
        Expression → IfExpr | LogicOrExpr
        """
        if self._check(TokenType.IF):
            return self._if_expr()
        return self._logic_or_expr()

    def _if_expr(self) -> IfExprNode:
        """
        IfExpr → if LogicOrExpr then Expression else Expression
        """
        if_tok = self._consume(TokenType.IF, "Expected 'if'.")
        cond = self._logic_or_expr()
        self._consume(TokenType.THEN, "Expected 'then' after condition.")
        then_branch = self._expression()
        self._consume(TokenType.ELSE, "Expected 'else' in if-expression.")
        else_branch = self._expression()

        # Type checks
        if cond.typ != BasicType.BOOL:
            raise self._error(if_tok, "Condition of if-expression must be bool.")

        if then_branch.typ is None or else_branch.typ is None:
            raise self._error(if_tok, "Internal error: missing type on if branches.")

        result_type = widened_type(then_branch.typ, else_branch.typ)
        if result_type is None:
            raise self._error(
                if_tok,
                f"Type error in if-expression branches: {then_branch.typ} vs {else_branch.typ}.",
            )

        node = IfExprNode(cond=cond, then_branch=then_branch, else_branch=else_branch)
        node.typ = result_type
        return node

    def _logic_or_expr(self) -> ExprNode:
        """
        LogicOrExpr → LogicAndExpr ('orelse' LogicAndExpr)*
        """
        left = self._logic_and_expr()
        while self._match(TokenType.ORELSE):
            op_tok = self._previous()
            right = self._logic_and_expr()

            if left.typ != BasicType.BOOL or right.typ != BasicType.BOOL:
                raise self._error(
                    op_tok,
                    "Operands of 'orelse' must both be bool.",
                )
            node = BinaryOpNode(op="orelse", left=left, right=right)
            node.typ = BasicType.BOOL
            left = node
        return left

    def _logic_and_expr(self) -> ExprNode:
        """
        LogicAndExpr → RelExpr ('andalso' RelExpr)*
        """
        left = self._rel_expr()
        while self._match(TokenType.ANDALSO):
            op_tok = self._previous()
            right = self._rel_expr()

            if left.typ != BasicType.BOOL or right.typ != BasicType.BOOL:
                raise self._error(
                    op_tok,
                    "Operands of 'andalso' must both be bool.",
                )
            node = BinaryOpNode(op="andalso", left=left, right=right)
            node.typ = BasicType.BOOL
            left = node
        return left

    def _rel_expr(self) -> ExprNode:
        """
        RelExpr → ArithExpr (CompOp ArithExpr)?
        CompOp  → '==' | '>' | '<'
        """
        left = self._arith_expr()

        # Comparison operator?
        if self._match(TokenType.EQUALS, TokenType.GREATER, TokenType.LESS):
            op_tok = self._previous()
            right = self._arith_expr()

            if left.typ is None or right.typ is None:
                raise self._error(op_tok, "Internal error: missing type on comparison operands.")

            # Comparison operands must be of the same type.
            if left.typ != right.typ:
                raise self._error(
                    op_tok,
                    f"Type error in comparison: operands must have same type, got {left.typ} and {right.typ}.",
                )

            node = BinaryOpNode(op=op_tok.value, left=left, right=right)
            node.typ = BasicType.BOOL
            return node

        return left

    def _arith_expr(self) -> ExprNode:
        """
        ArithExpr → Term (('+' | '-') Term)*
        """
        left = self._term()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._previous()
            right = self._term()

            if left.typ is None or right.typ is None:
                raise self._error(op_tok, "Internal error: missing type in arithmetic.")

            result_type = widened_type(left.typ, right.typ)
            if result_type is None:
                raise self._error(
                    op_tok,
                    f"Type error in arithmetic: incompatible types {left.typ} and {right.typ}.",
                )

            node = BinaryOpNode(op=op_tok.value, left=left, right=right)
            node.typ = result_type
            left = node
        return left

    def _term(self) -> ExprNode:
        """
        Term → Value (('*' | '/' | '//') Factor)*
        """
        self._record("Term -> Value (('*' | '/' | '//') Factor)*")
        left = self._value()
        while self._match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.INTDIV):
            op_tok = self._previous()
            right = self._factor()

            if left.typ is None or right.typ is None:
                raise self._error(op_tok, "Internal error: missing type in term.")

            result_type = widened_type(left.typ, right.typ)
            if result_type is None:
                raise self._error(
                    op_tok,
                    f"Type error in term: incompatible types {left.typ} and {right.typ}.",
                )

            node = BinaryOpNode(op=op_tok.value, left=left, right=right)
            node.typ = result_type
            left = node
        return left

    def _value(self) -> ExprNode:
        """
        Value → Factor | '-' Factor
        """
        if self._match(TokenType.MINUS):
            self._record("Value -> '-' Factor")
            op_tok = self._previous()
            operand = self._factor()
            if operand.typ not in (BasicType.INT, BasicType.LONG, BasicType.DOUBLE):
                raise self._error(
                    op_tok,
                    f"Unary '-' expects numeric operand, got {operand.typ}.",
                )
            node = UnaryOpNode(op="-", operand=operand)
            node.typ = operand.typ
            return node

        self._record("Value -> Factor")
        return self._factor()

    def _factor(self) -> ExprNode:
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
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        # identifier or function call
        if self._check(TokenType.IDENTIFIER):
            if self._peek_next().type == TokenType.LPAREN:
                self._record("Factor -> FunctionCall")
                return self._function_call()
            else:
                self._record("Factor -> IDENTIFIER")
                id_tok = self._advance()
                sym = self.current_scope.lookup(id_tok.value)
                if sym is None:
                    raise self._error(
                        id_tok,
                        f"Use of undeclared variable '{id_tok.value}'.",
                    )
                node = IdentifierExpr(name=id_tok.value)
                node.typ = sym.type
                return node

        # literals: bool, int, char, double
        if self._match(
            TokenType.TRUE,
            TokenType.FALSE,
            TokenType.INTLIT,
            TokenType.CHARLIT,
            TokenType.DOUBLELIT,
        ):
            lit_tok = self._previous()
            self._record("Factor -> literal")
            node = LiteralExpr(value=lit_tok.value)
            if lit_tok.type == TokenType.TRUE or lit_tok.type == TokenType.FALSE:
                node.typ = BasicType.BOOL
            elif lit_tok.type == TokenType.INTLIT:
                node.typ = BasicType.INT
            elif lit_tok.type == TokenType.DOUBLELIT:
                node.typ = BasicType.DOUBLE
            elif lit_tok.type == TokenType.CHARLIT:
                node.typ = BasicType.CHAR
            else:
                node.typ = None
            return node

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


# Convenience function

def parse_source(source: str) -> ProgramNode:
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
        program = parse_source(src)
        print("Parse succeeded.\n")

        print("=== SYMBOL TABLES ===")
        # parser is recreated here to access scopes; alternatively, refactor parse_source
        scanner = Scanner(src)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        program = parser.parse()
        for scope in parser.scopes:
            print(scope.pretty_print())
            print()

        print("=== AST ===")
        print(program.pretty())

    except ParseError as e:
        print("Parse / semantic error:", e)