"""Tests for the Anka interpreter."""

import pytest

from anka.grammar.parser import Parser
from anka.runtime.interpreter import Interpreter
from anka.runtime.interpreter import RuntimeError as AnkaRuntimeError


class TestInterpreterBasic:
    """Basic interpreter tests."""

    def test_interpreter_initializes(self) -> None:
        """Interpreter should initialize without error."""
        interpreter = Interpreter()
        assert interpreter is not None

    def test_execute_passthrough_no_steps(self) -> None:
        """Execute pipeline with no steps returns input directly."""
        parser = Parser()
        source = """
        PIPELINE passthrough:
            INPUT data: TABLE[x: INT]
            OUTPUT data
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        test_data = [{"x": 1}, {"x": 2}]
        result = interpreter.execute(ast, inputs={"data": test_data})

        assert result == test_data

    def test_execute_no_inputs_no_output(self) -> None:
        """Execute with no inputs returns None for missing output."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            OUTPUT data
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(AnkaRuntimeError):
            interpreter.execute(ast)


class TestInterpreterFilter:
    """Tests for FILTER operation execution."""

    def test_filter_greater_than(self) -> None:
        """Test FILTER with > operator."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_pos:
                FILTER data
                WHERE x > 0
                INTO positive
            OUTPUT positive
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 5}, {"x": -3}, {"x": 10}, {"x": 0}]}
        )

        assert result == [{"x": 5}, {"x": 10}]

    def test_filter_less_than(self) -> None:
        """Test FILTER with < operator."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_neg:
                FILTER data
                WHERE x < 0
                INTO negative
            OUTPUT negative
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 5}, {"x": -3}, {"x": 10}, {"x": -7}]}
        )

        assert result == [{"x": -3}, {"x": -7}]

    def test_filter_greater_than_or_equal(self) -> None:
        """Test FILTER with >= operator."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x >= 5
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 4}, {"x": 5}, {"x": 6}]}
        )

        assert result == [{"x": 5}, {"x": 6}]

    def test_filter_less_than_or_equal(self) -> None:
        """Test FILTER with <= operator."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x <= 5
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 4}, {"x": 5}, {"x": 6}]}
        )

        assert result == [{"x": 4}, {"x": 5}]

    def test_filter_equal(self) -> None:
        """Test FILTER with == operator."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x == 5
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 4}, {"x": 5}, {"x": 6}, {"x": 5}]}
        )

        assert result == [{"x": 5}, {"x": 5}]

    def test_filter_not_equal(self) -> None:
        """Test FILTER with != operator."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x != 5
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 4}, {"x": 5}, {"x": 6}]}
        )

        assert result == [{"x": 4}, {"x": 6}]

    def test_filter_with_string(self) -> None:
        """Test FILTER with string comparison."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"status": "active"},
                    {"status": "inactive"},
                    {"status": "active"},
                ]
            },
        )

        assert result == [{"status": "active"}, {"status": "active"}]

    def test_filter_with_decimal(self) -> None:
        """Test FILTER with decimal comparison."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[price: DECIMAL]
            STEP filter_cheap:
                FILTER data
                WHERE price < 100.0
                INTO cheap
            OUTPUT cheap
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [{"price": 50.0}, {"price": 150.0}, {"price": 99.99}]
            },
        )

        assert result == [{"price": 50.0}, {"price": 99.99}]

    def test_filter_no_matches(self) -> None:
        """Test FILTER that matches no rows."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x > 100
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 1}, {"x": 2}, {"x": 3}]}
        )

        assert result == []

    def test_filter_all_match(self) -> None:
        """Test FILTER that matches all rows."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x > 0
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        input_data = [{"x": 1}, {"x": 2}, {"x": 3}]
        result = interpreter.execute(ast, inputs={"data": input_data})

        assert result == input_data

    def test_filter_empty_input(self) -> None:
        """Test FILTER with empty input."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x > 0
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(ast, inputs={"data": []})

        assert result == []


class TestInterpreterMultipleSteps:
    """Tests for pipelines with multiple steps."""

    def test_multiple_steps_chained(self) -> None:
        """Test multiple steps that chain together."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"x": 5, "y": 1},
                    {"x": -3, "y": 2},
                    {"x": 10, "y": -1},
                    {"x": 7, "y": 3},
                ]
            },
        )

        assert result == [{"x": 5, "y": 1}, {"x": 7, "y": 3}]

    def test_hello_anka_example(self) -> None:
        """Test the hello.anka example from the documentation."""
        parser = Parser()
        source = """
        PIPELINE hello:
            INPUT data: TABLE[x: INT, y: INT]
            STEP filter_positive:
                FILTER data
                WHERE x > 0
                INTO positive_data
            OUTPUT positive_data
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"x": 5, "y": 1},
                    {"x": -3, "y": 2},
                    {"x": 10, "y": 3},
                ]
            },
        )

        assert result == [{"x": 5, "y": 1}, {"x": 10, "y": 3}]


class TestInterpreterErrors:
    """Tests for interpreter error handling."""

    def test_missing_source_data(self) -> None:
        """Test error when source data is not found."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER other_data
                WHERE x > 0
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(AnkaRuntimeError, match="Source 'other_data' not found"):
            interpreter.execute(ast, inputs={"data": [{"x": 1}]})

    def test_missing_output(self) -> None:
        """Test error when output variable is not found."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x > 0
                INTO result
            OUTPUT missing_output
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(
            AnkaRuntimeError, match="Output 'missing_output' not found"
        ):
            interpreter.execute(ast, inputs={"data": [{"x": 1}]})

    def test_missing_field_returns_false(self) -> None:
        """Test that missing field in row returns False (row excluded)."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP filter_step:
                FILTER data
                WHERE x > 0
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        # Row with missing 'x' field should be excluded
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 5}, {"y": 10}, {"x": 3}]}
        )

        assert result == [{"x": 5}, {"x": 3}]


class TestInterpreterMultipleFields:
    """Tests for rows with multiple fields."""

    def test_preserves_all_fields(self) -> None:
        """Test that filtering preserves all fields in matching rows."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT orders: TABLE[id: INT, customer: STRING, amount: DECIMAL]
            STEP filter_large:
                FILTER orders
                WHERE amount > 1000
                INTO large_orders
            OUTPUT large_orders
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "orders": [
                    {"id": 1, "customer": "Alice", "amount": 500},
                    {"id": 2, "customer": "Bob", "amount": 1500},
                    {"id": 3, "customer": "Charlie", "amount": 2000},
                ]
            },
        )

        assert result == [
            {"id": 2, "customer": "Bob", "amount": 1500},
            {"id": 3, "customer": "Charlie", "amount": 2000},
        ]


class TestInterpreterSelect:
    """Tests for SELECT operation execution."""

    def test_select_single_column(self) -> None:
        """Test SELECT with one column."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}]}
        )

        assert result == [{"x": 1}, {"x": 2}]

    def test_select_multiple_columns(self) -> None:
        """Test SELECT with multiple columns."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "orders": [
                    {"order_id": 1, "customer": "Alice", "amount": 100},
                    {"order_id": 2, "customer": "Bob", "amount": 200},
                ]
            },
        )

        assert result == [
            {"customer": "Alice", "amount": 100},
            {"customer": "Bob", "amount": 200},
        ]

    def test_select_preserves_column_order(self) -> None:
        """Test that SELECT preserves column order in output."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT, c: INT]
            STEP reorder:
                SELECT c, a
                FROM data
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"a": 1, "b": 2, "c": 3}]}
        )

        # Check that both columns are present
        assert result == [{"c": 3, "a": 1}]
        # Check column order is preserved (c before a)
        assert list(result[0].keys()) == ["c", "a"]

    def test_select_missing_column_error(self) -> None:
        """Test that SELECT raises error for non-existent column."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP pick:
                SELECT x, missing_col
                FROM data
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(
            AnkaRuntimeError, match="Column 'missing_col' not found"
        ):
            interpreter.execute(ast, inputs={"data": [{"x": 1}]})

    def test_select_missing_source_error(self) -> None:
        """Test that SELECT raises error for non-existent source."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP pick:
                SELECT x
                FROM missing_source
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(
            AnkaRuntimeError, match="Source 'missing_source' not found"
        ):
            interpreter.execute(ast, inputs={"data": [{"x": 1}]})

    def test_select_empty_input(self) -> None:
        """Test SELECT with empty input."""
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

        interpreter = Interpreter()
        result = interpreter.execute(ast, inputs={"data": []})

        assert result == []


class TestInterpreterFilterThenSelect:
    """Tests for combined FILTER and SELECT operations."""

    def test_filter_then_select(self) -> None:
        """Test a pipeline with FILTER followed by SELECT."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "orders": [
                    {"order_id": 1, "customer": "Alice", "amount": 1500, "status": "active"},
                    {"order_id": 2, "customer": "Bob", "amount": 500, "status": "pending"},
                    {"order_id": 3, "customer": "Carol", "amount": 2000, "status": "active"},
                ]
            },
        )

        assert result == [
            {"customer": "Alice", "amount": 1500},
            {"customer": "Carol", "amount": 2000},
        ]

    def test_select_then_filter(self) -> None:
        """Test a pipeline with SELECT followed by FILTER."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT, y: INT, z: INT]
            STEP pick_cols:
                SELECT x, y
                FROM data
                INTO subset
            STEP filter_pos:
                FILTER subset
                WHERE x > 0
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"x": 5, "y": 1, "z": 100},
                    {"x": -3, "y": 2, "z": 200},
                    {"x": 10, "y": 3, "z": 300},
                ]
            },
        )

        assert result == [{"x": 5, "y": 1}, {"x": 10, "y": 3}]


class TestInterpreterMap:
    """Tests for MAP operation execution."""

    def test_map_field_copy(self) -> None:
        """Test MAP with simple field reference."""
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

        interpreter = Interpreter()
        result = interpreter.execute(ast, inputs={"data": [{"x": 1}, {"x": 2}]})

        assert result == [{"x": 1, "y": 1}, {"x": 2, "y": 2}]

    def test_map_multiplication(self) -> None:
        """Test MAP with multiplication."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"quantity": 5, "price": 10.0},
                    {"quantity": 3, "price": 25.0},
                ]
            },
        )

        assert result == [
            {"quantity": 5, "price": 10.0, "total": 50.0},
            {"quantity": 3, "price": 25.0, "total": 75.0},
        ]

    def test_map_complex_expression(self) -> None:
        """Test MAP with complex arithmetic expression."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT]
            STEP calc:
                MAP data
                WITH score => (a + b) * 2
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"a": 3, "b": 7}]}
        )

        assert result == [{"a": 3, "b": 7, "score": 20}]

    def test_map_with_literal(self) -> None:
        """Test MAP with literal in expression."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"salary": 5000}]}
        )

        assert result == [{"salary": 5000, "total": 6000}]

    def test_map_missing_field_error(self) -> None:
        """Test MAP with missing field raises error."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP calc:
                MAP data
                WITH y => missing_field
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(AnkaRuntimeError, match="Field 'missing_field' not found"):
            interpreter.execute(ast, inputs={"data": [{"x": 1}]})


class TestInterpreterSort:
    """Tests for SORT operation execution."""

    def test_sort_asc(self) -> None:
        """Test SORT with ASC order."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 3}, {"x": 1}, {"x": 2}]}
        )

        assert result == [{"x": 1}, {"x": 2}, {"x": 3}]

    def test_sort_desc(self) -> None:
        """Test SORT with DESC order."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={"data": [{"amount": 100}, {"amount": 300}, {"amount": 200}]},
        )

        assert result == [{"amount": 300}, {"amount": 200}, {"amount": 100}]

    def test_sort_strings(self) -> None:
        """Test SORT with string values."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[name: STRING]
            STEP order:
                SORT data
                BY name ASC
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={"data": [{"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"}]},
        )

        assert result == [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]

    def test_sort_missing_key_error(self) -> None:
        """Test SORT with missing key raises error."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP order:
                SORT data
                BY missing_key ASC
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        with pytest.raises(AnkaRuntimeError, match="Sort key 'missing_key' not found"):
            interpreter.execute(ast, inputs={"data": [{"x": 1}]})

    def test_sort_nulls_last_asc(self) -> None:
        """Test SORT ASC with NULLS_LAST puts nulls at end."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[id: INT, price: DECIMAL]
            STEP order:
                SORT data
                BY price ASC NULLS_LAST
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"id": 1, "price": 30.0},
                    {"id": 2, "price": None},
                    {"id": 3, "price": 10.0},
                    {"id": 4, "price": 20.0},
                ]
            },
        )

        assert result == [
            {"id": 3, "price": 10.0},
            {"id": 4, "price": 20.0},
            {"id": 1, "price": 30.0},
            {"id": 2, "price": None},
        ]

    def test_sort_nulls_first_asc(self) -> None:
        """Test SORT ASC with NULLS_FIRST puts nulls at start."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[id: INT, price: DECIMAL]
            STEP order:
                SORT data
                BY price ASC NULLS_FIRST
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"id": 1, "price": 30.0},
                    {"id": 2, "price": None},
                    {"id": 3, "price": 10.0},
                ]
            },
        )

        assert result == [
            {"id": 2, "price": None},
            {"id": 3, "price": 10.0},
            {"id": 1, "price": 30.0},
        ]

    def test_sort_default_null_handling_asc(self) -> None:
        """Test SORT ASC without NULLS clause defaults to nulls at end."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[id: INT, price: DECIMAL]
            STEP order:
                SORT data
                BY price ASC
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"id": 1, "price": 30.0},
                    {"id": 2, "price": None},
                    {"id": 3, "price": 10.0},
                ]
            },
        )

        # Default for ASC: nulls at end (like SQL NULLS LAST)
        assert result == [
            {"id": 3, "price": 10.0},
            {"id": 1, "price": 30.0},
            {"id": 2, "price": None},
        ]

    def test_sort_nulls_last_desc(self) -> None:
        """Test SORT DESC with NULLS_LAST puts nulls at end."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[id: INT, price: DECIMAL]
            STEP order:
                SORT data
                BY price DESC NULLS_LAST
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"id": 1, "price": 30.0},
                    {"id": 2, "price": None},
                    {"id": 3, "price": 10.0},
                ]
            },
        )

        assert result == [
            {"id": 1, "price": 30.0},
            {"id": 3, "price": 10.0},
            {"id": 2, "price": None},
        ]


class TestInterpreterLimit:
    """Tests for LIMIT operation execution."""

    def test_limit_basic(self) -> None:
        """Test LIMIT takes correct count."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP take:
                LIMIT data
                COUNT 2
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}]}
        )

        assert result == [{"x": 1}, {"x": 2}]

    def test_limit_more_than_available(self) -> None:
        """Test LIMIT with count greater than rows returns all."""
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

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 1}, {"x": 2}]}
        )

        assert result == [{"x": 1}, {"x": 2}]

    def test_limit_zero(self) -> None:
        """Test LIMIT with count 0 returns empty."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            STEP take:
                LIMIT data
                COUNT 0
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast, inputs={"data": [{"x": 1}, {"x": 2}]}
        )

        assert result == []


class TestInterpreterFullPipeline:
    """Tests for full pipelines with all operations."""

    def test_sales_report_pipeline(self) -> None:
        """Test the complete sales report pipeline."""
        parser = Parser()
        ast = parser.parse_file("examples/sales_report.anka")

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "sales": [
                    {"product": "Widget", "quantity": 5, "price": 10.0},
                    {"product": "Gadget", "quantity": 3, "price": 25.0},
                    {"product": "Gizmo", "quantity": 0, "price": 15.0},
                    {"product": "Doohickey", "quantity": 10, "price": 5.0},
                    {"product": "Thingamajig", "quantity": 2, "price": 50.0},
                ]
            },
        )

        # Expected: filtered (quantity > 0), computed total, sorted DESC, top 3, selected columns
        # Widget: 5 * 10 = 50
        # Gadget: 3 * 25 = 75
        # Doohickey: 10 * 5 = 50
        # Thingamajig: 2 * 50 = 100
        # Sorted DESC: 100, 75, 50, 50 -> top 3 = 100, 75, 50
        assert result == [
            {"product": "Thingamajig", "total": 100.0},
            {"product": "Gadget", "total": 75.0},
            {"product": "Widget", "total": 50.0},
        ]

    def test_filter_map_sort_limit_select(self) -> None:
        """Test full pipeline: FILTER → MAP → SORT → LIMIT → SELECT."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT, y: INT]
            STEP filter_pos:
                FILTER data
                WHERE x > 0
                INTO positive
            STEP add_sum:
                MAP positive
                WITH sum => x + y
                INTO with_sum
            STEP order:
                SORT with_sum
                BY sum DESC
                INTO sorted
            STEP take:
                LIMIT sorted
                COUNT 2
                INTO top
            STEP pick:
                SELECT x, sum
                FROM top
                INTO result
            OUTPUT result
        """
        ast = parser.parse(source)

        interpreter = Interpreter()
        result = interpreter.execute(
            ast,
            inputs={
                "data": [
                    {"x": 5, "y": 1},    # sum = 6
                    {"x": -3, "y": 10},  # filtered out
                    {"x": 10, "y": 5},   # sum = 15
                    {"x": 2, "y": 3},    # sum = 5
                ]
            },
        )

        # After filter: (5,1), (10,5), (2,3)
        # After map: sums = 6, 15, 5
        # After sort DESC: 15, 6, 5
        # After limit 2: 15, 6
        # After select: x and sum only
        assert result == [
            {"x": 10, "sum": 15},
            {"x": 5, "sum": 6},
        ]
