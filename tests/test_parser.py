"""Tests for the Anka parser."""

from pathlib import Path

import pytest
from lark.exceptions import LarkError

from anka.ast.nodes import (
    ArithmeticOp,
    BinaryOp,
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
)
from anka.grammar.parser import Parser

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


class TestParserBasic:
    """Basic parser functionality tests."""

    def test_parse_hello_anka(self) -> None:
        """Parse the hello.anka example file."""
        parser = Parser()
        ast = parser.parse_file(EXAMPLES_DIR / "hello.anka")

        # Verify it's a Pipeline
        assert isinstance(ast, Pipeline)
        assert ast.name.name == "hello"

        # Verify it has one input
        assert len(ast.inputs) == 1
        input_node = ast.inputs[0]
        assert isinstance(input_node, Input)
        assert input_node.name.name == "data"

        # Verify input type is TABLE[x: INT, y: INT]
        assert isinstance(input_node.type_expr, TableType)
        assert len(input_node.type_expr.fields) == 2
        assert input_node.type_expr.fields[0].name.name == "x"
        assert input_node.type_expr.fields[0].type_name.name == "INT"
        assert input_node.type_expr.fields[1].name.name == "y"
        assert input_node.type_expr.fields[1].type_name.name == "INT"

        # Verify it has one step
        assert len(ast.steps) == 1
        step = ast.steps[0]
        assert isinstance(step, Step)
        assert step.name.name == "filter_positive"
        assert isinstance(step.operation, Filter)
        assert step.operation.source.name == "data"
        assert step.operation.target.name == "positive_data"

        # Verify output
        assert ast.outputs is not None
        assert isinstance(ast.outputs, Output)
        assert ast.outputs.name.name == "positive_data"

    def test_parse_minimal_pipeline(self) -> None:
        """Parse a minimal pipeline from string."""
        parser = Parser()
        source = """
        PIPELINE minimal:
            INPUT foo: TABLE[a: STRING]
            OUTPUT foo
        """
        ast = parser.parse(source)

        assert isinstance(ast, Pipeline)
        assert ast.name.name == "minimal"
        assert len(ast.inputs) == 1
        assert ast.inputs[0].name.name == "foo"

    def test_parse_multiple_fields(self) -> None:
        """Parse a table with multiple fields."""
        parser = Parser()
        source = """
        PIPELINE multi_field:
            INPUT orders: TABLE[id: INT, name: STRING, price: DECIMAL, active: BOOL]
            OUTPUT orders
        """
        ast = parser.parse(source)

        assert isinstance(ast, Pipeline)
        fields = ast.inputs[0].type_expr.fields
        assert len(fields) == 4

        assert fields[0].name.name == "id"
        assert fields[0].type_name.name == "INT"

        assert fields[1].name.name == "name"
        assert fields[1].type_name.name == "STRING"

        assert fields[2].name.name == "price"
        assert fields[2].type_name.name == "DECIMAL"

        assert fields[3].name.name == "active"
        assert fields[3].type_name.name == "BOOL"


class TestParserStepsAndFilter:
    """Tests for STEP and FILTER parsing."""

    def test_parse_step_with_filter(self) -> None:
        """Parse a pipeline with STEP and FILTER."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT orders: TABLE[amount: DECIMAL]
            STEP filter_large:
                FILTER orders
                WHERE amount > 1000
                INTO large_orders
            OUTPUT large_orders
        """
        ast = parser.parse(source)

        # Verify pipeline structure
        assert isinstance(ast, Pipeline)
        assert ast.name.name == "test"
        assert len(ast.inputs) == 1
        assert len(ast.steps) == 1

        # Verify step
        step = ast.steps[0]
        assert isinstance(step, Step)
        assert step.name.name == "filter_large"

        # Verify filter operation
        assert isinstance(step.operation, Filter)
        assert step.operation.source.name == "orders"
        assert step.operation.target.name == "large_orders"

        # Verify condition
        condition = step.operation.condition
        assert isinstance(condition, BinaryOp)
        assert condition.left.name == "amount"
        assert condition.operator == ">"
        assert isinstance(condition.right, Literal)
        assert condition.right.value == 1000
        assert condition.right.literal_type == "NUMBER"

    def test_parse_filter_with_decimal(self) -> None:
        """Parse a FILTER with a decimal literal."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[price: DECIMAL]
            STEP filter_cheap:
                FILTER data
                WHERE price < 99.99
                INTO cheap
            OUTPUT cheap
        """
        ast = parser.parse(source)

        condition = ast.steps[0].operation.condition
        assert condition.operator == "<"
        assert condition.right.value == 99.99
        assert condition.right.literal_type == "NUMBER"

    def test_parse_filter_with_string(self) -> None:
        """Parse a FILTER with a string literal."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[status: STRING]
            STEP filter_active:
                FILTER data
                WHERE status == "active"
                INTO active
            OUTPUT active
        """
        ast = parser.parse(source)

        condition = ast.steps[0].operation.condition
        assert condition.operator == "=="
        assert condition.right.value == "active"
        assert condition.right.literal_type == "STRING"

    def test_parse_all_comparison_operators(self) -> None:
        """Parse FILTER with all comparison operators."""
        parser = Parser()
        operators = [">", "<", ">=", "<=", "==", "!="]

        for op in operators:
            source = f"""
            PIPELINE test:
                INPUT data: TABLE[x: INT]
                STEP filter_step:
                    FILTER data
                    WHERE x {op} 10
                    INTO result
                OUTPUT result
            """
            ast = parser.parse(source)
            assert ast.steps[0].operation.condition.operator == op

    def test_parse_multiple_steps(self) -> None:
        """Parse a pipeline with multiple steps."""
        parser = Parser()
        source = """
        PIPELINE multi_step:
            INPUT data: TABLE[x: INT, y: INT]
            STEP step1:
                FILTER data
                WHERE x > 0
                INTO positive_x
            STEP step2:
                FILTER positive_x
                WHERE y > 0
                INTO positive_both
            OUTPUT positive_both
        """
        ast = parser.parse(source)

        assert len(ast.steps) == 2
        assert ast.steps[0].name.name == "step1"
        assert ast.steps[0].operation.source.name == "data"
        assert ast.steps[0].operation.target.name == "positive_x"
        assert ast.steps[1].name.name == "step2"
        assert ast.steps[1].operation.source.name == "positive_x"
        assert ast.steps[1].operation.target.name == "positive_both"


class TestParserSourceLocations:
    """Tests for source location tracking."""

    def test_pipeline_has_location(self) -> None:
        """Pipeline node should have source location."""
        parser = Parser()
        source = "PIPELINE test:\n    INPUT x: TABLE[a: INT]\n    OUTPUT x"
        ast = parser.parse(source)

        assert ast.source_location is not None
        assert ast.source_location.line >= 1

    def test_identifier_has_location(self) -> None:
        """Identifiers should have source locations."""
        parser = Parser()
        source = "PIPELINE test:\n    INPUT x: TABLE[a: INT]\n    OUTPUT x"
        ast = parser.parse(source)

        assert ast.name.source_location is not None
        assert ast.name.source_location.line >= 1


class TestParserErrors:
    """Tests for parser error handling."""

    def test_missing_output(self) -> None:
        """Should fail on missing OUTPUT."""
        parser = Parser()
        source = """
        PIPELINE incomplete:
            INPUT data: TABLE[x: INT]
        """
        with pytest.raises(LarkError):
            parser.parse(source)

    def test_invalid_syntax(self) -> None:
        """Should fail on invalid syntax."""
        parser = Parser()
        source = "This is not valid Ankah"
        with pytest.raises(LarkError):
            parser.parse(source)


class TestParserSelect:
    """Tests for SELECT operation parsing."""

    def test_parse_select_single_column(self) -> None:
        """Parse a SELECT with one column."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT, y: INT]
            STEP pick:
                SELECT x
                FROM data
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        assert len(ast.steps) == 1
        step = ast.steps[0]
        assert isinstance(step.operation, Select)
        assert step.operation.source.name == "data"
        assert step.operation.target.name == "result"
        assert len(step.operation.columns) == 1
        assert step.operation.columns[0].name == "x"

    def test_parse_select_multiple_columns(self) -> None:
        """Parse a SELECT with multiple columns."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT orders: TABLE[order_id: INT, customer: STRING, amount: DECIMAL]
            STEP pick_cols:
                SELECT customer, amount
                FROM orders
                INTO summary
            OUTPUT summary
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Select)
        assert len(step.operation.columns) == 2
        assert step.operation.columns[0].name == "customer"
        assert step.operation.columns[1].name == "amount"

    def test_parse_filter_then_select(self) -> None:
        """Parse a pipeline with both FILTER and SELECT."""
        parser = Parser()
        source = """
        PIPELINE summarize_orders:
            INPUT orders: TABLE[order_id: INT, customer: STRING, amount: DECIMAL, status: STRING]
            STEP filter_large:
                FILTER orders
                WHERE amount > 1000
                INTO large_orders
            STEP pick_columns:
                SELECT customer, amount
                FROM large_orders
                INTO summary
            OUTPUT summary
        """
        ast = parser.parse(source)

        assert len(ast.steps) == 2

        # First step is FILTER
        step1 = ast.steps[0]
        assert isinstance(step1.operation, Filter)
        assert step1.name.name == "filter_large"
        assert step1.operation.source.name == "orders"
        assert step1.operation.target.name == "large_orders"

        # Second step is SELECT
        step2 = ast.steps[1]
        assert isinstance(step2.operation, Select)
        assert step2.name.name == "pick_columns"
        assert step2.operation.source.name == "large_orders"
        assert step2.operation.target.name == "summary"
        assert len(step2.operation.columns) == 2

    def test_parse_select_preserves_column_order(self) -> None:
        """Column order in SELECT should be preserved."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT, c: INT]
            STEP reorder:
                SELECT c, a, b
                FROM data
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Select)
        columns = [col.name for col in step.operation.columns]
        assert columns == ["c", "a", "b"]


class TestParserMap:
    """Tests for MAP operation parsing."""

    def test_parse_map_simple(self) -> None:
        """Parse a MAP with simple field reference."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP copy:
                MAP data
                WITH y => x
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Map)
        assert step.operation.source.name == "data"
        assert step.operation.new_column.name == "y"
        assert step.operation.target.name == "result"
        assert isinstance(step.operation.expression, Identifier)
        assert step.operation.expression.name == "x"

    def test_parse_map_with_arithmetic(self) -> None:
        """Parse a MAP with arithmetic expression."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[quantity: INT, price: DECIMAL]
            STEP calc:
                MAP data
                WITH total => quantity * price
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Map)
        assert step.operation.new_column.name == "total"
        assert isinstance(step.operation.expression, ArithmeticOp)
        assert step.operation.expression.operator == "*"

    def test_parse_map_with_parentheses(self) -> None:
        """Parse a MAP with parenthesized expression."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT]
            STEP calc:
                MAP data
                WITH result => (a + b) * 2
                INTO output
            OUTPUT output
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Map)
        expr = step.operation.expression
        assert isinstance(expr, ArithmeticOp)
        assert expr.operator == "*"
        assert isinstance(expr.left, ArithmeticOp)
        assert expr.left.operator == "+"
        assert isinstance(expr.right, Literal)
        assert expr.right.value == 2

    def test_parse_map_with_literal(self) -> None:
        """Parse a MAP with literal in expression."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[salary: INT]
            STEP bonus:
                MAP data
                WITH total => salary + 1000
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Map)
        expr = step.operation.expression
        assert isinstance(expr, ArithmeticOp)
        assert expr.operator == "+"
        assert isinstance(expr.right, Literal)
        assert expr.right.value == 1000


class TestParserSort:
    """Tests for SORT operation parsing."""

    def test_parse_sort_asc(self) -> None:
        """Parse a SORT with ASC order."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP order:
                SORT data
                BY x ASC
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Sort)
        assert step.operation.source.name == "data"
        assert step.operation.key.name == "x"
        assert step.operation.descending is False
        assert step.operation.target.name == "result"

    def test_parse_sort_desc(self) -> None:
        """Parse a SORT with DESC order."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[amount: DECIMAL]
            STEP order:
                SORT data
                BY amount DESC
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Sort)
        assert step.operation.key.name == "amount"
        assert step.operation.descending is True


class TestParserLimit:
    """Tests for LIMIT operation parsing."""

    def test_parse_limit(self) -> None:
        """Parse a LIMIT operation."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP take:
                LIMIT data
                COUNT 10
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        step = ast.steps[0]
        assert isinstance(step.operation, Limit)
        assert step.operation.source.name == "data"
        assert step.operation.count == 10
        assert step.operation.target.name == "result"


class TestParserFullPipeline:
    """Tests for full pipelines with all operations."""

    def test_parse_sales_report(self) -> None:
        """Parse the sales_report.anka example."""
        parser = Parser()
        ast = parser.parse_file(EXAMPLES_DIR / "sales_report.anka")

        assert isinstance(ast, Pipeline)
        assert ast.name.name == "sales_report"
        assert len(ast.inputs) == 1
        assert len(ast.steps) == 5

        # Check operation types in order
        assert isinstance(ast.steps[0].operation, Filter)
        assert isinstance(ast.steps[1].operation, Map)
        assert isinstance(ast.steps[2].operation, Sort)
        assert isinstance(ast.steps[3].operation, Limit)
        assert isinstance(ast.steps[4].operation, Select)
