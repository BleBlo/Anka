"""Tests for semantic analysis."""

import pytest

from anka.semantic.symbols import Scope, Symbol, SymbolTable


class TestSymbolTable:
    """Tests for the symbol table."""

    def test_define_and_lookup(self) -> None:
        """Should define and look up symbols."""
        table = SymbolTable()
        symbol = Symbol(name="x")
        table.define(symbol)

        found = table.lookup("x")
        assert found is not None
        assert found.name == "x"

    def test_lookup_not_found(self) -> None:
        """Should return None for undefined symbols."""
        table = SymbolTable()
        assert table.lookup("undefined") is None

    def test_nested_scopes(self) -> None:
        """Should look up in parent scopes."""
        table = SymbolTable()
        outer = Symbol(name="outer")
        table.define(outer)

        table.enter_scope("inner")
        inner = Symbol(name="inner")
        table.define(inner)

        # Can find both symbols from inner scope
        assert table.lookup("outer") is not None
        assert table.lookup("inner") is not None

        # Exit inner scope
        table.exit_scope()

        # Can still find outer, but not inner
        assert table.lookup("outer") is not None
        assert table.lookup("inner") is None


class TestScope:
    """Tests for individual scopes."""

    def test_duplicate_definition(self) -> None:
        """Should raise on duplicate definition in same scope."""
        scope: Scope[Symbol] = Scope(name="test")
        scope.define(Symbol(name="x"))

        with pytest.raises(ValueError, match="already defined"):
            scope.define(Symbol(name="x"))

    def test_local_lookup(self) -> None:
        """Local lookup should not check parent."""
        parent: Scope[Symbol] = Scope(name="parent")
        parent.define(Symbol(name="x"))

        child: Scope[Symbol] = Scope(name="child", parent=parent)

        # lookup finds in parent
        assert child.lookup("x") is not None

        # lookup_local does not
        assert child.lookup_local("x") is None
