"""Visitor pattern for AST traversal."""

from typing import Any, TypeVar

from anka.ast.nodes import (
    ArithmeticOp,
    ASTNode,
    BinaryOp,
    FieldDef,
    Filter,
    Identifier,
    Input,
    Limit,
    Literal,
    Map,
    Output,
    Pipeline,
    Select,
    Sort,
    Step,
    TableType,
    TypeName,
)

T = TypeVar("T")


class ASTVisitor:
    """Base visitor class for traversing the AST.

    Subclass this and override visit_* methods for specific node types.
    Default behavior is to visit all children.
    """

    def visit(self, node: ASTNode) -> Any:
        """Dispatch to the appropriate visit method based on node type."""
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        """Default visitor that does nothing.

        Override this to change default behavior for unhandled node types.
        """

    def visit_Pipeline(self, node: Pipeline) -> Any:
        """Visit a Pipeline node."""
        self.visit(node.name)
        for input_node in node.inputs:
            self.visit(input_node)
        for step_node in node.steps:
            self.visit(step_node)
        if node.outputs:
            self.visit(node.outputs)

    def visit_Input(self, node: Input) -> Any:
        """Visit an Input node."""
        self.visit(node.name)
        self.visit(node.type_expr)

    def visit_Output(self, node: Output) -> Any:
        """Visit an Output node."""
        self.visit(node.name)

    def visit_Step(self, node: Step) -> Any:
        """Visit a Step node."""
        self.visit(node.name)
        self.visit(node.operation)

    def visit_Filter(self, node: Filter) -> Any:
        """Visit a Filter node."""
        self.visit(node.source)
        self.visit(node.condition)
        self.visit(node.target)

    def visit_Select(self, node: Select) -> Any:
        """Visit a Select node."""
        for col in node.columns:
            self.visit(col)
        self.visit(node.source)
        self.visit(node.target)

    def visit_Map(self, node: Map) -> Any:
        """Visit a Map node."""
        self.visit(node.source)
        self.visit(node.new_column)
        self.visit(node.expression)
        self.visit(node.target)

    def visit_Sort(self, node: Sort) -> Any:
        """Visit a Sort node."""
        self.visit(node.source)
        self.visit(node.key)
        self.visit(node.target)

    def visit_Limit(self, node: Limit) -> Any:
        """Visit a Limit node."""
        self.visit(node.source)
        self.visit(node.target)

    def visit_ArithmeticOp(self, node: ArithmeticOp) -> Any:
        """Visit an ArithmeticOp node."""
        self.visit(node.left)
        self.visit(node.right)

    def visit_BinaryOp(self, node: BinaryOp) -> Any:
        """Visit a BinaryOp node."""
        self.visit(node.left)
        self.visit(node.right)

    def visit_Literal(self, node: Literal) -> Any:
        """Visit a Literal node."""
        self.generic_visit(node)

    def visit_TableType(self, node: TableType) -> Any:
        """Visit a TableType node."""
        for field_node in node.fields:
            self.visit(field_node)

    def visit_FieldDef(self, node: FieldDef) -> Any:
        """Visit a FieldDef node."""
        self.visit(node.name)
        self.visit(node.type_name)

    def visit_Identifier(self, node: Identifier) -> Any:
        """Visit an Identifier node."""
        self.generic_visit(node)

    def visit_TypeName(self, node: TypeName) -> Any:
        """Visit a TypeName node."""
        self.generic_visit(node)


class ASTPrinter(ASTVisitor):
    """Visitor that prints the AST in a readable format."""

    def __init__(self) -> None:
        """Initialize the printer with zero indentation."""
        self._indent = 0
        self._output: list[str] = []

    def _emit(self, text: str) -> None:
        """Emit a line with current indentation."""
        self._output.append("  " * self._indent + text)

    def get_output(self) -> str:
        """Get the accumulated output as a string."""
        return "\n".join(self._output)

    def visit_Pipeline(self, node: Pipeline) -> None:
        """Print a Pipeline node."""
        self._emit(f"Pipeline: {node.name.name}")
        self._indent += 1
        self._emit("Inputs:")
        self._indent += 1
        for input_node in node.inputs:
            self.visit(input_node)
        self._indent -= 1
        if node.steps:
            self._emit("Steps:")
            self._indent += 1
            for step_node in node.steps:
                self.visit(step_node)
            self._indent -= 1
        if node.outputs:
            self._emit("Output:")
            self._indent += 1
            self.visit(node.outputs)
            self._indent -= 1
        self._indent -= 1

    def visit_Input(self, node: Input) -> None:
        """Print an Input node."""
        self._emit(f"Input: {node.name.name}")
        self._indent += 1
        self.visit(node.type_expr)
        self._indent -= 1

    def visit_Output(self, node: Output) -> None:
        """Print an Output node."""
        self._emit(f"Output: {node.name.name}")

    def visit_Step(self, node: Step) -> None:
        """Print a Step node."""
        self._emit(f"Step: {node.name.name}")
        self._indent += 1
        self.visit(node.operation)
        self._indent -= 1

    def visit_Filter(self, node: Filter) -> None:
        """Print a Filter node."""
        self._emit(f"Filter: {node.source.name} -> {node.target.name}")
        self._indent += 1
        self._emit("Where:")
        self._indent += 1
        self.visit(node.condition)
        self._indent -= 1
        self._indent -= 1

    def visit_Select(self, node: Select) -> None:
        """Print a Select node."""
        columns = ", ".join(col.name for col in node.columns)
        self._emit(f"Select: {node.source.name} -> {node.target.name}")
        self._indent += 1
        self._emit(f"Columns: {columns}")
        self._indent -= 1

    def visit_Map(self, node: Map) -> None:
        """Print a Map node."""
        self._emit(f"Map: {node.source.name} -> {node.target.name}")
        self._indent += 1
        self._emit(f"New column: {node.new_column.name}")
        self._emit(f"Expression: {self._format_arith(node.expression)}")
        self._indent -= 1

    def visit_Sort(self, node: Sort) -> None:
        """Print a Sort node."""
        order = "DESC" if node.descending else "ASC"
        self._emit(f"Sort: {node.source.name} -> {node.target.name}")
        self._indent += 1
        self._emit(f"By: {node.key.name} {order}")
        self._indent -= 1

    def visit_Limit(self, node: Limit) -> None:
        """Print a Limit node."""
        self._emit(f"Limit: {node.source.name} -> {node.target.name}")
        self._indent += 1
        self._emit(f"Count: {node.count}")
        self._indent -= 1

    def _format_arith(self, node: Any) -> str:
        """Format an arithmetic expression as a string."""
        if isinstance(node, ArithmeticOp):
            left = self._format_arith(node.left)
            right = self._format_arith(node.right)
            return f"({left} {node.operator} {right})"
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, Literal):
            return str(node.value)
        return str(node)

    def visit_BinaryOp(self, node: BinaryOp) -> None:
        """Print a BinaryOp node."""
        self._emit(f"{node.left.name} {node.operator} {node.right.value}")

    def visit_TableType(self, node: TableType) -> None:
        """Print a TableType node."""
        self._emit("TableType:")
        self._indent += 1
        for field_node in node.fields:
            self.visit(field_node)
        self._indent -= 1

    def visit_FieldDef(self, node: FieldDef) -> None:
        """Print a FieldDef node."""
        self._emit(f"Field: {node.name.name}: {node.type_name.name}")
