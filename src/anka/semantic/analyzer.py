"""Semantic analyzer for type checking and validation."""

from anka.ast.nodes import Pipeline
from anka.semantic.symbols import SymbolTable


class SemanticAnalyzer:
    """Performs semantic analysis on the AST.

    Currently a stub - will be implemented to:
    - Build symbol tables
    - Check type consistency
    - Validate references
    - Report semantic errors
    """

    def __init__(self) -> None:
        """Initialize the semantic analyzer."""
        self._symbol_table = SymbolTable()
        self._errors: list[str] = []

    def analyze(self, ast: Pipeline) -> list[str]:
        """Analyze the AST for semantic errors.

        Args:
            ast: The Pipeline AST to analyze.

        Returns:
            List of error messages (empty if valid).
        """
        # TODO: Implement semantic analysis
        # - Register inputs in symbol table
        # - Check output references valid inputs
        # - Type check operations
        _ = ast  # Mark as used for now
        self._errors = []
        return self._errors

    @property
    def symbol_table(self) -> SymbolTable:
        """Get the symbol table built during analysis."""
        return self._symbol_table
