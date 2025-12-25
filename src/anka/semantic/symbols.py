"""Symbol table with linked scopes for semantic analysis."""

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

from anka.ast.nodes import SourceLocation, TableType

T = TypeVar("T")


@dataclass
class Symbol:
    """A symbol in the symbol table.

    Attributes:
        name: The symbol's identifier.
        type_info: Type information for the symbol.
        source_location: Where the symbol was defined.
        is_input: Whether this is a pipeline input.
        is_output: Whether this is a pipeline output.
    """

    name: str
    type_info: Optional[TableType] = None
    source_location: Optional[SourceLocation] = None
    is_input: bool = False
    is_output: bool = False


@dataclass
class Scope(Generic[T]):
    """A scope in the symbol table with parent reference.

    Attributes:
        name: Name of this scope (e.g., pipeline name).
        parent: Parent scope for lookup chain.
        symbols: Symbols defined in this scope.
    """

    name: str
    parent: Optional["Scope[T]"] = None
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def define(self, symbol: Symbol) -> None:
        """Define a symbol in this scope.

        Args:
            symbol: The symbol to define.

        Raises:
            ValueError: If symbol is already defined in this scope.
        """
        if symbol.name in self.symbols:
            raise ValueError(f"Symbol '{symbol.name}' already defined in scope '{self.name}'")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol by name, checking parent scopes.

        Args:
            name: The symbol name to look up.

        Returns:
            The symbol if found, None otherwise.
        """
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope only (no parent lookup).

        Args:
            name: The symbol name to look up.

        Returns:
            The symbol if found in this scope, None otherwise.
        """
        return self.symbols.get(name)


class SymbolTable:
    """Symbol table managing a stack of scopes.

    The symbol table maintains a current scope and allows
    entering/exiting nested scopes while preserving parent
    references for name lookup.
    """

    def __init__(self) -> None:
        """Initialize with a global scope."""
        self._global_scope: Scope[Symbol] = Scope(name="global")
        self._current_scope: Scope[Symbol] = self._global_scope

    @property
    def current_scope(self) -> Scope[Symbol]:
        """Get the current scope."""
        return self._current_scope

    def enter_scope(self, name: str) -> Scope[Symbol]:
        """Enter a new nested scope.

        Args:
            name: Name for the new scope.

        Returns:
            The newly created scope.
        """
        new_scope: Scope[Symbol] = Scope(name=name, parent=self._current_scope)
        self._current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Scope[Symbol]:
        """Exit the current scope and return to parent.

        Returns:
            The scope that was exited.

        Raises:
            RuntimeError: If trying to exit the global scope.
        """
        if self._current_scope.parent is None:
            raise RuntimeError("Cannot exit global scope")
        exited = self._current_scope
        self._current_scope = self._current_scope.parent
        return exited

    def define(self, symbol: Symbol) -> None:
        """Define a symbol in the current scope.

        Args:
            symbol: The symbol to define.
        """
        self._current_scope.define(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol starting from current scope.

        Args:
            name: The symbol name to look up.

        Returns:
            The symbol if found, None otherwise.
        """
        return self._current_scope.lookup(name)
