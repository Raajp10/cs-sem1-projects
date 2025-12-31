# Grammar Specification (Mini-Language)

This file contains the **refactored LL(1) grammar** used by the manual recursive-descent parser.

## 1. High-level

Program      → StmtList EOF
StmtList     → Stmt StmtList | ε

Stmt         → DeclareStmt
             | AssignStmt
             | FunctionDefStmt
             | FunctionCallStmt
             | Block

Block        → '{' StmtList '}'

## 2. Declarations

DeclareStmt  → Type IdList ';'
Type         → int | double | bool | char | long
IdList       → IDENTIFIER IdListTail
IdListTail   → ',' IDENTIFIER IdListTail | ε

## 3. Assignment

AssignStmt   → IDENTIFIER AssignOp Expression ';'
AssignOp     → '=' | '+=' | '-=' | '*=' | '/='

## 4. Functions

FunctionDefStmt → fun IDENTIFIER '(' ParamList? ')' '=' Expression ';'
ParamList       → Type IDENTIFIER ParamListTail
ParamListTail   → ',' Type IDENTIFIER ParamListTail | ε

FunctionCallStmt → FunctionCall ';'
FunctionCall     → IDENTIFIER '(' ArgList? ')'
ArgList          → Expression ArgListTail
ArgListTail      → ',' Expression ArgListTail | ε

## 5. Expressions

Expression   → IfExpr | BoolExpr
IfExpr       → if BoolExpr then Expression else Expression

BoolExpr     → BoolTerm BoolExprPrime
BoolExprPrime→ 'orelse' BoolTerm BoolExprPrime | ε

BoolTerm     → BoolFactor BoolTermPrime
BoolTermPrime→ 'andalso' BoolFactor BoolTermPrime | ε

BoolFactor   → BoolLiteral
             | Comparison
             | '(' BoolExpr ')'
BoolLiteral  → true | false

Comparison   → ArithExpr ComparisonTail
ComparisonTail → CompOp ArithExpr | ε
CompOp       → '==' | '>' | '<'

ArithExpr    → Term ArithExprPrime
ArithExprPrime → '+' Term ArithExprPrime
               | '-' Term ArithExprPrime
               | ε

Term         → Value TermPrime
TermPrime    → '*' Factor TermPrime
             | '/' Factor TermPrime
             | '//' Factor TermPrime
             | ε

Value        → Factor
             | '-' Factor

Factor       → '(' ArithExpr ')'
             | FunctionCall
             | IDENTIFIER
             | INTLIT
             | DOUBLELIT
             | CHARLIT

