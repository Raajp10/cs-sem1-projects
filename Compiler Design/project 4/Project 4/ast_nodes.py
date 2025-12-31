# ast_nodes.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from symbol_table import BasicType


# -------- Base Classes --------

class ASTNode:
    def pretty(self, indent: int = 0) -> str:
        raise NotImplementedError


@dataclass
class StmtNode(ASTNode):
    """Base class for statement nodes."""
    # No fields here; subclasses define their own.


@dataclass
class ExprNode(ASTNode):
    """
    Base class for expression nodes.

    `typ` holds the static type (BasicType) after semantic analysis.
    We set `init=False` so it is NOT part of the dataclass __init__,
    avoiding the "non-default argument follows default" issue in subclasses.
    """
    typ: Optional[BasicType] = field(default=None, init=False)


# -------- Program / Block --------

@dataclass
class ProgramNode(ASTNode):
    # Exactly one child per non-declaration statement (flattened).
    statements: List[StmtNode] = field(default_factory=list)

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Program"]
        for stmt in self.statements:
            lines.append(stmt.pretty(indent + 1))
        return "\n".join(lines)


@dataclass
class BlockNode(StmtNode):
    statements: List[StmtNode] = field(default_factory=list)

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Block"]
        for stmt in self.statements:
            lines.append(stmt.pretty(indent + 1))
        return "\n".join(lines)


# -------- Statements --------

@dataclass
class AssignNode(StmtNode):
    name: str
    op: str     # "=", "+=", etc.
    expr: ExprNode

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Assign({self.name} {self.op})"]
        lines.append(self.expr.pretty(indent + 1))
        return "\n".join(lines)


@dataclass
class FunctionDefNode(StmtNode):
    name: str
    param_names: List[str]
    param_types: List[BasicType]
    body: ExprNode

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        params = ", ".join(
            f"{t} {n}" for t, n in zip(self.param_types, self.param_names)
        )
        lines = [f"{pad}FunctionDef {self.name}({params})"]
        lines.append(self.body.pretty(indent + 1))
        return "\n".join(lines)


@dataclass
class FunctionCallStmtNode(StmtNode):
    call: "FunctionCallExpr"

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}FunctionCallStmt"]
        lines.append(self.call.pretty(indent + 1))
        return "\n".join(lines)


# -------- Expressions --------

@dataclass
class IfExprNode(ExprNode):
    cond: ExprNode
    then_branch: ExprNode
    else_branch: ExprNode

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}IfExpr"]
        lines.append(self.cond.pretty(indent + 1))
        lines.append(self.then_branch.pretty(indent + 1))
        lines.append(self.else_branch.pretty(indent + 1))
        return "\n".join(lines)


@dataclass
class BinaryOpNode(ExprNode):
    op: str
    left: ExprNode
    right: ExprNode

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}BinaryOp('{self.op}')"]
        lines.append(self.left.pretty(indent + 1))
        lines.append(self.right.pretty(indent + 1))
        return "\n".join(lines)


@dataclass
class UnaryOpNode(ExprNode):
    op: str
    operand: ExprNode

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}UnaryOp('{self.op}')"]
        lines.append(self.operand.pretty(indent + 1))
        return "\n".join(lines)


@dataclass
class IdentifierExpr(ExprNode):
    name: str

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        typ_str = f": {self.typ}" if self.typ is not None else ""
        return f"{pad}Identifier({self.name}{typ_str})"


@dataclass
class LiteralExpr(ExprNode):
    value: str

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        typ_str = f": {self.typ}" if self.typ is not None else ""
        return f"{pad}Literal({self.value}{typ_str})"


@dataclass
class FunctionCallExpr(ExprNode):
    name: str
    args: List[ExprNode] = field(default_factory=list)

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        lines = [f"{pad}Call {self.name}"]
        for arg in self.args:
            lines.append(arg.pretty(indent + 1))
        return "\n".join(lines)