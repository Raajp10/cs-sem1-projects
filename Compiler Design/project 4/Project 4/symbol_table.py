# symbol_table.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List


class BasicType(Enum):
    INT = auto()
    LONG = auto()
    DOUBLE = auto()
    BOOL = auto()
    CHAR = auto()

    def __str__(self) -> str:
        return self.name.lower()


# Widening chain: int -> long -> double
WIDENING_ORDER = {
    BasicType.INT: 0,
    BasicType.LONG: 1,
    BasicType.DOUBLE: 2,
    BasicType.BOOL: 0,   # not really numeric, but assign an order
    BasicType.CHAR: 0,   # same here
}


def can_widen(src: BasicType, dst: BasicType) -> bool:
    """Return True if src can be widened to dst."""
    if src == dst:
        return True
    # Only int/long/double are truly numeric-widened
    numeric = {BasicType.INT, BasicType.LONG, BasicType.DOUBLE}
    if src in numeric and dst in numeric:
        return WIDENING_ORDER[src] <= WIDENING_ORDER[dst]
    # For non-numeric types, require exact match
    return False


def widened_type(left: BasicType, right: BasicType) -> Optional[BasicType]:
    """Return the widened type of two operands, or None if incompatible."""
    if left == right:
        return left
    numeric = {BasicType.INT, BasicType.LONG, BasicType.DOUBLE}
    if left in numeric and right in numeric:
        # choose the one with larger widening rank
        return max((left, right), key=lambda t: WIDENING_ORDER[t])
    return None


@dataclass
class Symbol:
    name: str
    type: BasicType
    offset: int


class SymbolTable:
    """
    Single scope symbol table with parent link (for nested scopes),
    as in Engineering a Compiler Chapter 4.
    """

    def __init__(self, parent: Optional["SymbolTable"] = None, scope_name: str = "anon"):
        self.parent = parent
        self.scope_name = scope_name
        self.entries: Dict[str, Symbol] = {}
        self._next_offset: int = 0  # in bytes

    # ------------- Declaration / Lookup -------------

    def declare(self, name: str, typ: BasicType, size: int) -> Symbol:
        """Insert a new symbol in the *current* scope. Error if duplicate."""
        if name in self.entries:
            raise ValueError(f"Duplicate declaration of '{name}' in scope '{self.scope_name}'.")
        sym = Symbol(name=name, type=typ, offset=self._next_offset)
        self.entries[name] = sym
        self._next_offset += size
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up name in this scope or any parent scope."""
        table: Optional[SymbolTable] = self
        while table is not None:
            sym = table.entries.get(name)
            if sym is not None:
                return sym
            table = table.parent
        return None

    # ------------- Debug / Printing -------------

    def flatten_scopes(self) -> List["SymbolTable"]:
        """
        Return all symbol tables in the chain from this one up to the global.
        (Primarily for debugging; main driver will hold its own list of scopes.)
        """
        scopes = []
        cur: Optional[SymbolTable] = self
        while cur is not None:
            scopes.append(cur)
            cur = cur.parent
        return scopes

    def pretty_print(self) -> str:
        lines = [f"Scope '{self.scope_name}':"]
        lines.append(f"{'Name':<15}{'Type':<10}{'Offset':<10}")
        lines.append("-" * 35)
        for sym in self.entries.values():
            lines.append(f"{sym.name:<15}{str(sym.type):<10}{sym.offset:<10}")
        return "\n".join(lines)
