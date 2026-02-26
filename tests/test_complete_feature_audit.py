"""Comprehensive Feature Audit for Anka DSL.

This test file verifies EVERY feature in Anka works correctly.
Each feature is tested in isolation and in combination with others.
"""

import pytest
from anka.grammar.parser import Parser
from anka.runtime.interpreter import Interpreter


def parse(code: str):
    """Helper function to parse Anka code."""
    parser = Parser()
    return parser.parse(code)


def run(code: str, inputs: dict = None):
    """Helper to parse and execute Anka code."""
    parser = Parser()
    ast = parser.parse(code)
    interpreter = Interpreter()
    return interpreter.execute(ast, inputs=inputs or {})


class TestDataOperations:
    """Test all data manipulation operations."""

    def test_filter_with_comparison_operators(self) -> None:
        """Test FILTER with all comparison operators."""
        code = '''
        PIPELINE test_filter:
            INPUT data: TABLE[value: INT, name: STRING]
            STEP s1: FILTER data WHERE value > 10 INTO r1
            OUTPUT r1
        '''
        result = run(code, {"data": [
            {"value": 5, "name": "a"},
            {"value": 10, "name": "b"},
            {"value": 15, "name": "c"}
        ]})
        assert result == [{"value": 15, "name": "c"}]

    def test_filter_equals(self) -> None:
        """Test FILTER with == operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: FILTER data WHERE value == 10 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 5},
            {"value": 10},
            {"value": 15}
        ]})
        assert result == [{"value": 10}]

    def test_filter_with_null_checks(self) -> None:
        """Test FILTER with IS_NULL and IS_NOT_NULL."""
        code = '''
        PIPELINE test_null:
            INPUT data: TABLE[value: INT]
            STEP s1: FILTER data WHERE value IS_NULL INTO nulls
            OUTPUT nulls
        '''
        result = run(code, {"data": [
            {"value": 1},
            {"value": None},
            {"value": 3}
        ]})
        assert result == [{"value": None}]

    def test_filter_not_null(self) -> None:
        """Test FILTER with IS_NOT_NULL."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: FILTER data WHERE value IS_NOT_NULL INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 1},
            {"value": None},
            {"value": 3}
        ]})
        assert result == [{"value": 1}, {"value": 3}]

    def test_filter_with_in_check(self) -> None:
        """Test FILTER with IN clause."""
        code = '''
        PIPELINE test_in:
            INPUT data: TABLE[status: STRING]
            STEP s1: FILTER data WHERE status IN ("active", "pending") INTO filtered
            OUTPUT filtered
        '''
        result = run(code, {"data": [
            {"status": "active"},
            {"status": "inactive"},
            {"status": "pending"}
        ]})
        assert len(result) == 2

    def test_filter_with_between(self) -> None:
        """Test FILTER with BETWEEN clause."""
        code = '''
        PIPELINE test_between:
            INPUT data: TABLE[value: INT]
            STEP s1: FILTER data WHERE value BETWEEN 5 AND 15 INTO filtered
            OUTPUT filtered
        '''
        result = run(code, {"data": [
            {"value": 1},
            {"value": 5},
            {"value": 10},
            {"value": 15},
            {"value": 20}
        ]})
        assert len(result) == 3

    def test_filter_with_and(self) -> None:
        """Test FILTER with AND operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT]
            STEP s1: FILTER data WHERE a > 5 AND b < 10 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"a": 3, "b": 5},
            {"a": 7, "b": 5},
            {"a": 7, "b": 15}
        ]})
        assert result == [{"a": 7, "b": 5}]

    def test_filter_with_or(self) -> None:
        """Test FILTER with OR operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT]
            STEP s1: FILTER data WHERE a > 10 OR b < 3 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"a": 5, "b": 1},
            {"a": 15, "b": 10}
        ]})
        assert len(result) == 2

    def test_filter_with_not(self) -> None:
        """Test FILTER with NOT operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: FILTER data WHERE NOT value > 5 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 3},
            {"value": 7}
        ]})
        assert result == [{"value": 3}]

    def test_select_operation(self) -> None:
        """Test SELECT to pick specific columns."""
        code = '''
        PIPELINE test_select:
            INPUT data: TABLE[a: INT, b: INT, c: INT]
            STEP s1: SELECT a, b FROM data INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"a": 1, "b": 2, "c": 3}]})
        assert result == [{"a": 1, "b": 2}]

    def test_map_operation(self) -> None:
        """Test MAP to create computed columns."""
        code = '''
        PIPELINE test_map:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH doubled => value * 2 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"value": 5}]})
        assert result[0]["doubled"] == 10

    def test_sort_asc(self) -> None:
        """Test SORT with ASC."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: SORT data BY value ASC INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 3},
            {"value": 1},
            {"value": 2}
        ]})
        assert result == [{"value": 1}, {"value": 2}, {"value": 3}]

    def test_sort_desc(self) -> None:
        """Test SORT with DESC."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: SORT data BY value DESC INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 3},
            {"value": 1},
            {"value": 2}
        ]})
        assert result == [{"value": 3}, {"value": 2}, {"value": 1}]

    def test_sort_with_nulls_first(self) -> None:
        """Test SORT with NULLS_FIRST."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: SORT data BY value ASC NULLS_FIRST INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 2},
            {"value": None},
            {"value": 1}
        ]})
        assert result[0]["value"] is None

    def test_sort_with_nulls_last(self) -> None:
        """Test SORT with NULLS_LAST."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: SORT data BY value ASC NULLS_LAST INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 2},
            {"value": None},
            {"value": 1}
        ]})
        assert result[-1]["value"] is None

    def test_limit_operation(self) -> None:
        """Test LIMIT to take first N rows."""
        code = '''
        PIPELINE test_limit:
            INPUT data: TABLE[value: INT]
            STEP s1: LIMIT data COUNT 2 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"value": i} for i in range(5)]})
        assert len(result) == 2

    def test_skip_operation(self) -> None:
        """Test SKIP to skip first N rows."""
        code = '''
        PIPELINE test_skip:
            INPUT data: TABLE[value: INT]
            STEP s1: SKIP data COUNT 2 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"value": i} for i in range(5)]})
        assert len(result) == 3
        assert result[0]["value"] == 2

    def test_distinct_operation(self) -> None:
        """Test DISTINCT to remove duplicates."""
        code = '''
        PIPELINE test_distinct:
            INPUT data: TABLE[category: STRING]
            STEP s1: DISTINCT data BY category INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"category": "a"},
            {"category": "b"},
            {"category": "a"}
        ]})
        assert len(result) == 2

    def test_aggregate_count(self) -> None:
        """Test AGGREGATE with COUNT."""
        code = '''
        PIPELINE test_count:
            INPUT data: TABLE[category: STRING]
            STEP s1: AGGREGATE data COMPUTE COUNT() AS total INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"category": "a"},
            {"category": "b"},
            {"category": "a"}
        ]})
        assert result[0]["total"] == 3

    def test_aggregate_sum(self) -> None:
        """Test AGGREGATE with SUM."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: AGGREGATE data COMPUTE SUM(value) AS total INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]})
        assert result[0]["total"] == 60

    def test_aggregate_avg(self) -> None:
        """Test AGGREGATE with AVG."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: AGGREGATE data COMPUTE AVG(value) AS avg INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]})
        assert result[0]["avg"] == 20.0

    def test_aggregate_with_group_by(self) -> None:
        """Test AGGREGATE with GROUP_BY."""
        code = '''
        PIPELINE test_group:
            INPUT data: TABLE[category: STRING, value: INT]
            STEP s1: AGGREGATE data GROUP_BY category COMPUTE SUM(value) AS total INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"category": "a", "value": 10},
            {"category": "a", "value": 20},
            {"category": "b", "value": 5}
        ]})
        a_group = next(r for r in result if r["category"] == "a")
        assert a_group["total"] == 30

    def test_aggregate_min_max(self) -> None:
        """Test AGGREGATE with MIN and MAX."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: AGGREGATE data COMPUTE MIN(value) AS min_val, MAX(value) AS max_val INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 5},
            {"value": 10},
            {"value": 3}
        ]})
        assert result[0]["min_val"] == 3
        assert result[0]["max_val"] == 10


class TestJoinOperations:
    """Test JOIN and LEFT_JOIN operations."""

    def test_inner_join(self) -> None:
        """Test JOIN (inner join)."""
        code = '''
        PIPELINE test_join:
            INPUT orders: TABLE[id: INT, customer_id: INT]
            INPUT customers: TABLE[id: INT, name: STRING]
            STEP s1: JOIN orders WITH customers ON orders.customer_id == customers.id INTO result
            OUTPUT result
        '''
        result = run(code, {
            "orders": [
                {"id": 1, "customer_id": 100},
                {"id": 2, "customer_id": 200},
                {"id": 3, "customer_id": 999}
            ],
            "customers": [
                {"id": 100, "name": "Alice"},
                {"id": 200, "name": "Bob"}
            ]
        })
        assert len(result) == 2

    def test_left_join(self) -> None:
        """Test LEFT_JOIN (left outer join)."""
        code = '''
        PIPELINE test:
            INPUT orders: TABLE[id: INT, customer_id: INT]
            INPUT customers: TABLE[id: INT, name: STRING]
            STEP s1: LEFT_JOIN orders WITH customers ON orders.customer_id == customers.id INTO result
            OUTPUT result
        '''
        result = run(code, {
            "orders": [
                {"id": 1, "customer_id": 100},
                {"id": 2, "customer_id": 999}
            ],
            "customers": [
                {"id": 100, "name": "Alice"}
            ]
        })
        assert len(result) == 2


class TestColumnOperations:
    """Test column manipulation operations."""

    def test_rename_operation(self) -> None:
        """Test RENAME to rename columns."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[old_name: STRING]
            STEP s1: RENAME data WITH old_name AS new_name INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"old_name": "test"}]})
        assert "new_name" in result[0]
        assert "old_name" not in result[0]

    def test_rename_multiple_columns(self) -> None:
        """Test RENAME with multiple columns."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT]
            STEP s1: RENAME data WITH a AS x WITH b AS y INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"a": 1, "b": 2}]})
        assert result[0] == {"x": 1, "y": 2}

    def test_drop_operation(self) -> None:
        """Test DROP to remove columns."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT, c: INT]
            STEP s1: DROP data COLUMNS b, c INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"a": 1, "b": 2, "c": 3}]})
        assert result[0] == {"a": 1}

    def test_add_column_operation(self) -> None:
        """Test ADD_COLUMN with default value."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            STEP s1: ADD_COLUMN data COLUMN status DEFAULT "active" INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"id": 1}, {"id": 2}]})
        assert all(r["status"] == "active" for r in result)


class TestSetOperations:
    """Test set operations (UNION, SLICE)."""

    def test_union_operation(self) -> None:
        """Test UNION to combine tables."""
        code = '''
        PIPELINE test:
            INPUT a: TABLE[value: INT]
            INPUT b: TABLE[value: INT]
            STEP s1: UNION a WITH b INTO result
            OUTPUT result
        '''
        result = run(code, {
            "a": [{"value": 1}, {"value": 2}],
            "b": [{"value": 2}, {"value": 3}]
        })
        values = [r["value"] for r in result]
        assert sorted(values) == [1, 2, 3]

    def test_union_all_operation(self) -> None:
        """Test UNION_ALL keeps duplicates."""
        code = '''
        PIPELINE test:
            INPUT a: TABLE[value: INT]
            INPUT b: TABLE[value: INT]
            STEP s1: UNION_ALL a WITH b INTO result
            OUTPUT result
        '''
        result = run(code, {
            "a": [{"value": 1}, {"value": 2}],
            "b": [{"value": 2}, {"value": 3}]
        })
        assert len(result) == 4

    def test_slice_operation(self) -> None:
        """Test SLICE for pagination."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: SLICE data FROM 1 TO 3 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"value": i} for i in range(5)]})
        assert len(result) == 2
        assert result[0]["value"] == 1
        assert result[1]["value"] == 2


class TestMathFunctions:
    """Test all math functions."""

    def test_abs_function(self) -> None:
        """Test ABS function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => ABS(value) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": -5}]})
        assert result[0]["result"] == 5

    def test_round_function(self) -> None:
        """Test ROUND function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: DECIMAL]
            STEP s1: MAP data WITH result => ROUND(value, 2) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 3.14159}]})
        assert result[0]["result"] == 3.14

    def test_floor_function(self) -> None:
        """Test FLOOR function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: DECIMAL]
            STEP s1: MAP data WITH result => FLOOR(value) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 3.7}]})
        assert result[0]["result"] == 3

    def test_ceil_function(self) -> None:
        """Test CEIL function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: DECIMAL]
            STEP s1: MAP data WITH result => CEIL(value) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 3.2}]})
        assert result[0]["result"] == 4

    def test_mod_function(self) -> None:
        """Test MOD function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => MOD(value, 3) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 10}]})
        assert result[0]["result"] == 1

    def test_power_function(self) -> None:
        """Test POWER function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => POWER(value, 2) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 4}]})
        assert result[0]["result"] == 16

    def test_sqrt_function(self) -> None:
        """Test SQRT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => SQRT(value) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 16}]})
        assert result[0]["result"] == 4.0

    def test_sign_function(self) -> None:
        """Test SIGN function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => SIGN(value) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": -5}]})
        assert result[0]["result"] == -1

    def test_trunc_function(self) -> None:
        """Test TRUNC function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: DECIMAL]
            STEP s1: MAP data WITH result => TRUNC(value) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": -3.7}]})
        assert result[0]["result"] == -3

    def test_min_max_val_functions(self) -> None:
        """Test MIN_VAL and MAX_VAL functions."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[a: INT, b: INT]
            STEP s1: MAP data WITH min_val => MIN_VAL(a, b) INTO t1
            STEP s2: MAP t1 WITH max_val => MAX_VAL(a, b) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"a": 5, "b": 10}]})
        assert result[0]["min_val"] == 5
        assert result[0]["max_val"] == 10

    def test_negative_numbers(self) -> None:
        """Test negative number literals."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => value + -5 INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 20}]})
        assert result[0]["result"] == 15


class TestStringFunctions:
    """Test all string functions."""

    def test_upper_function(self) -> None:
        """Test UPPER function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[name: STRING]
            STEP s1: MAP data WITH result => UPPER(name) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"name": "hello"}]})
        assert result[0]["result"] == "HELLO"

    def test_lower_function(self) -> None:
        """Test LOWER function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[name: STRING]
            STEP s1: MAP data WITH result => LOWER(name) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"name": "HELLO"}]})
        assert result[0]["result"] == "hello"

    def test_trim_function(self) -> None:
        """Test TRIM function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH result => TRIM(text) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "  hello  "}]})
        assert result[0]["result"] == "hello"

    def test_length_function(self) -> None:
        """Test LENGTH function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH len => LENGTH(text) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "hello"}]})
        assert result[0]["len"] == 5

    def test_substring_function(self) -> None:
        """Test SUBSTRING function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH sub => SUBSTRING(text, 0, 3) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "hello"}]})
        assert result[0]["sub"] == "hel"

    def test_left_function(self) -> None:
        """Test LEFT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH result => LEFT(text, 3) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "hello"}]})
        assert result[0]["result"] == "hel"

    def test_right_function(self) -> None:
        """Test RIGHT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH result => RIGHT(text, 2) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "hello"}]})
        assert result[0]["result"] == "lo"

    def test_replace_all_function(self) -> None:
        """Test REPLACE_ALL function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH result => REPLACE_ALL(text, "o", "0") INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "hello world"}]})
        assert result[0]["result"] == "hell0 w0rld"

    def test_concat_function(self) -> None:
        """Test CONCAT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[first: STRING, last: STRING]
            STEP s1: MAP data WITH full => CONCAT(first, " ", last) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"first": "John", "last": "Doe"}]})
        assert result[0]["full"] == "John Doe"

    def test_pad_left_function(self) -> None:
        """Test PAD_LEFT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[num: STRING]
            STEP s1: MAP data WITH result => PAD_LEFT(num, 5, "0") INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"num": "42"}]})
        assert result[0]["result"] == "00042"

    def test_contains_check(self) -> None:
        """Test CONTAINS in FILTER."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[name: STRING]
            STEP s1: FILTER data WHERE CONTAINS(name, "test") INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"name": "testing"},
            {"name": "hello"}
        ]})
        assert len(result) == 1

    def test_starts_with_check(self) -> None:
        """Test STARTS_WITH in FILTER."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[name: STRING]
            STEP s1: FILTER data WHERE STARTS_WITH(name, "pre") INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"name": "prefix"},
            {"name": "suffix"}
        ]})
        assert len(result) == 1

    def test_ends_with_check(self) -> None:
        """Test ENDS_WITH in FILTER."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[name: STRING]
            STEP s1: FILTER data WHERE ENDS_WITH(name, "ing") INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"name": "testing"},
            {"name": "nothing"},
            {"name": "test"}
        ]})
        assert len(result) == 2


class TestTypeCasting:
    """Test type casting functions."""

    def test_to_int_function(self) -> None:
        """Test TO_INT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH num => TO_INT(text) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "42"}]})
        assert result[0]["num"] == 42
        assert isinstance(result[0]["num"], int)

    def test_to_string_function(self) -> None:
        """Test TO_STRING function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[num: INT]
            STEP s1: MAP data WITH text => TO_STRING(num) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"num": 42}]})
        assert result[0]["text"] == "42"

    def test_to_decimal_function(self) -> None:
        """Test TO_DECIMAL function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH num => TO_DECIMAL(text) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "3.14"}]})
        assert abs(result[0]["num"] - 3.14) < 0.001

    def test_to_bool_function(self) -> None:
        """Test TO_BOOL function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH flag => TO_BOOL(text) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"text": "true"}]})
        assert result[0]["flag"] is True


class TestTypeChecking:
    """Test type checking functions."""

    def test_is_int_check(self) -> None:
        """Test IS_INT function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: FILTER data WHERE IS_INT(value) INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": 42},
            {"value": "text"},
            {"value": 3.14}
        ]})
        assert len(result) == 1

    def test_is_string_check(self) -> None:
        """Test IS_STRING function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: STRING]
            STEP s1: FILTER data WHERE IS_STRING(value) INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": "text"},
            {"value": 42}
        ]})
        assert len(result) == 1

    def test_is_empty_check(self) -> None:
        """Test IS_EMPTY function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: STRING]
            STEP s1: FILTER data WHERE IS_EMPTY(value) INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [
            {"value": ""},
            {"value": "text"},
            {"value": []},
            {"value": [1, 2]}
        ]})
        assert len(result) == 2


class TestListFunctions:
    """Test list functions."""

    def test_first_function(self) -> None:
        """Test FIRST function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[items: STRING]
            STEP s1: MAP data WITH first_item => FIRST(items) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"items": [1, 2, 3, 4, 5]}]})
        assert result[0]["first_item"] == 1

    def test_last_function(self) -> None:
        """Test LAST function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[items: STRING]
            STEP s1: MAP data WITH last_item => LAST(items) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"items": [1, 2, 3, 4, 5]}]})
        assert result[0]["last_item"] == 5

    def test_nth_function(self) -> None:
        """Test NTH function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[items: STRING]
            STEP s1: MAP data WITH third => NTH(items, 2) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"items": ["a", "b", "c", "d"]}]})
        assert result[0]["third"] == "c"

    def test_unique_function(self) -> None:
        """Test UNIQUE function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[items: STRING]
            STEP s1: MAP data WITH unique_items => UNIQUE(items) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"items": [1, 2, 2, 3, 3, 3]}]})
        assert len(result[0]["unique_items"]) == 3

    def test_flatten_function(self) -> None:
        """Test FLATTEN function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[items: STRING]
            STEP s1: MAP data WITH flat => FLATTEN(items) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"items": [[1, 2], [3, 4]]}]})
        assert result[0]["flat"] == [1, 2, 3, 4]

    def test_list_contains_function(self) -> None:
        """Test LIST_CONTAINS function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[items: STRING]
            STEP s1: MAP data WITH has_three => LIST_CONTAINS(items, 3) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"items": [1, 2, 3, 4, 5]}]})
        assert result[0]["has_three"] is True

    def test_range_function(self) -> None:
        """Test RANGE function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            STEP s1: MAP data WITH nums => RANGE(0, 5) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"id": 1}]})
        assert result[0]["nums"] == [0, 1, 2, 3, 4]


class TestConditionalExpressions:
    """Test IF and NULLIF expressions."""

    def test_if_expression(self) -> None:
        """Test inline IF expression."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH category => IF(value > 10, "high", "low") INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [
            {"value": 5},
            {"value": 15}
        ]})
        assert result[0]["category"] == "low"
        assert result[1]["category"] == "high"

    def test_nullif_expression(self) -> None:
        """Test NULLIF expression."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => NULLIF(value, 0) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [
            {"value": 5},
            {"value": 0}
        ]})
        assert result[0]["result"] == 5
        assert result[1]["result"] is None

    def test_coalesce_expression(self) -> None:
        """Test COALESCE expression."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => COALESCE(value, 0) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [
            {"value": 5},
            {"value": None}
        ]})
        assert result[0]["result"] == 5
        assert result[1]["result"] == 0


class TestControlFlow:
    """Test control flow statements."""

    def test_set_statement_with_booleans(self) -> None:
        """Test SET with TRUE/FALSE."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET is_active = TRUE
            SET is_deleted = FALSE
            SET count = 0
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        assert interpreter.get_scalar("is_active") is True
        assert interpreter.get_scalar("is_deleted") is False
        assert interpreter.get_scalar("count") == 0

    def test_if_else_statement(self) -> None:
        """Test IF/ELSE statement."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET count = 5
            SET result = 0
            IF count > 3:
                SET result = 1
            ELSE:
                SET result = 2
            END
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        assert interpreter.get_scalar("result") == 1

    def test_for_each_statement(self) -> None:
        """Test FOR_EACH loop."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET total = 0
            FOR_EACH item IN data:
                SET total = total + 1
            END
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": [{"id": 1}, {"id": 2}, {"id": 3}]})
        assert interpreter.get_scalar("total") == 3

    def test_while_statement(self) -> None:
        """Test WHILE loop."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET counter = 0
            WHILE counter < 5:
                SET counter = counter + 1
            END
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        assert interpreter.get_scalar("counter") == 5

    def test_break_statement(self) -> None:
        """Test BREAK in loop."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET counter = 0
            WHILE counter < 100:
                SET counter = counter + 1
                IF counter == 3:
                    BREAK
                END
            END
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        assert interpreter.get_scalar("counter") == 3

    def test_continue_statement(self) -> None:
        """Test CONTINUE in loop."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET sum = 0
            SET counter = 0
            WHILE counter < 5:
                SET counter = counter + 1
                IF counter == 3:
                    CONTINUE
                END
                SET sum = sum + counter
            END
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        # sum = 1 + 2 + 4 + 5 = 12 (skipping 3)
        assert interpreter.get_scalar("sum") == 12

    def test_match_statement(self) -> None:
        """Test MATCH/CASE statement."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET status = "active"
            SET result = ""
            MATCH status:
                CASE "active":
                    SET result = "is active"
                CASE "inactive":
                    SET result = "is inactive"
                DEFAULT:
                    SET result = "unknown"
            END
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        assert interpreter.get_scalar("result") == "is active"

    def test_assert_statement(self) -> None:
        """Test ASSERT statement."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET count = 5
            ASSERT count > 0 MESSAGE "count must be positive"
            OUTPUT data
        '''
        # Should not raise
        run(code, {"data": []})

    def test_return_statement(self) -> None:
        """Test RETURN statement."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            SET x = 1
            RETURN data
            SET x = 2
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": [{"id": 1}]})
        assert interpreter.get_scalar("x") == 1


class TestPrintAndLog:
    """Test PRINT and LOG statements."""

    def test_print_statement(self) -> None:
        """Test PRINT statement."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            PRINT "Hello World"
            PRINT 42
            OUTPUT data
        '''
        run(code, {"data": []})

    def test_log_statements(self) -> None:
        """Test LOG_INFO, LOG_WARN, LOG_ERROR, LOG_DEBUG."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            LOG_INFO "Info message"
            LOG_WARN "Warning message"
            LOG_ERROR "Error message"
            LOG_DEBUG "Debug message"
            OUTPUT data
        '''
        run(code, {"data": []})


class TestComments:
    """Test comment syntax."""

    def test_single_line_comments(self) -> None:
        """Test -- comments are ignored."""
        code = '''
        -- This is a comment
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            -- Another comment
            SET x = 5
            OUTPUT data
        '''
        parser = Parser()
        ast = parser.parse(code)
        interpreter = Interpreter()
        interpreter.execute(ast, inputs={"data": []})
        assert interpreter.get_scalar("x") == 5


class TestArithmetic:
    """Test arithmetic operations."""

    def test_addition(self) -> None:
        """Test + operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => value + 10 INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 20}]})
        assert result[0]["result"] == 30

    def test_subtraction(self) -> None:
        """Test - operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => value - 5 INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 20}]})
        assert result[0]["result"] == 15

    def test_multiplication(self) -> None:
        """Test * operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => value * 2 INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 20}]})
        assert result[0]["result"] == 40

    def test_division(self) -> None:
        """Test / operator."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => value / 2 INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 20}]})
        assert result[0]["result"] == 10

    def test_arithmetic_with_parentheses(self) -> None:
        """Test parentheses in arithmetic."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH result => (value + 10) * 2 INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 5}]})
        assert result[0]["result"] == 30


class TestDateFunctions:
    """Test date/time functions."""

    def test_now_function(self) -> None:
        """Test NOW function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            STEP s1: MAP data WITH current_time => NOW() INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"id": 1}]})
        assert result[0]["current_time"] is not None

    def test_today_function(self) -> None:
        """Test TODAY function."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            STEP s1: MAP data WITH current_date => TODAY() INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"id": 1}]})
        assert result[0]["current_date"] is not None

    def test_year_function(self) -> None:
        """Test YEAR function."""
        from datetime import datetime
        code = '''
        PIPELINE test:
            INPUT data: TABLE[date: STRING]
            STEP s1: MAP data WITH year => YEAR(date) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"date": datetime(2024, 6, 15)}]})
        assert result[0]["year"] == 2024

    def test_month_function(self) -> None:
        """Test MONTH function."""
        from datetime import datetime
        code = '''
        PIPELINE test:
            INPUT data: TABLE[date: STRING]
            STEP s1: MAP data WITH month => MONTH(date) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"date": datetime(2024, 6, 15)}]})
        assert result[0]["month"] == 6

    def test_day_function(self) -> None:
        """Test DAY function."""
        from datetime import datetime
        code = '''
        PIPELINE test:
            INPUT data: TABLE[date: STRING]
            STEP s1: MAP data WITH day => DAY(date) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"date": datetime(2024, 6, 15)}]})
        assert result[0]["day"] == 15

    def test_add_days_function(self) -> None:
        """Test ADD_DAYS function."""
        from datetime import datetime
        code = '''
        PIPELINE test:
            INPUT data: TABLE[date: STRING]
            STEP s1: MAP data WITH future => ADD_DAYS(date, 7) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"date": datetime(2024, 1, 1)}]})
        assert result[0]["future"].day == 8

    def test_diff_days_function(self) -> None:
        """Test DIFF_DAYS function."""
        from datetime import datetime
        code = '''
        PIPELINE test:
            INPUT data: TABLE[start: STRING, end: STRING]
            STEP s1: MAP data WITH days_between => DIFF_DAYS(end, start) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{
            "start": datetime(2024, 1, 1),
            "end": datetime(2024, 1, 11)
        }]})
        assert result[0]["days_between"] == 10


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_data_pipeline(self) -> None:
        """Test a complete data transformation pipeline."""
        code = '''
        PIPELINE full:
            INPUT orders: TABLE[id: INT, customer: STRING, amount: DECIMAL, status: STRING]
            STEP s1: FILTER orders WHERE status == "active" INTO active
            STEP s2: MAP active WITH discounted => amount * 0.9 INTO discounted_orders
            STEP s3: SORT discounted_orders BY amount DESC INTO sorted_orders
            STEP s4: LIMIT sorted_orders COUNT 3 INTO top
            OUTPUT top
        '''
        result = run(code, {"orders": [
            {"id": 1, "customer": "Alice", "amount": 100, "status": "active"},
            {"id": 2, "customer": "Bob", "amount": 200, "status": "inactive"},
            {"id": 3, "customer": "Charlie", "amount": 300, "status": "active"},
            {"id": 4, "customer": "David", "amount": 400, "status": "active"},
            {"id": 5, "customer": "Eve", "amount": 500, "status": "active"},
        ]})
        assert len(result) == 3
        assert result[0]["discounted"] == 450  # 500 * 0.9

    def test_aggregation_pipeline(self) -> None:
        """Test aggregation with grouping."""
        code = '''
        PIPELINE agg:
            INPUT sales: TABLE[region: STRING, product: STRING, amount: DECIMAL]
            STEP s1: AGGREGATE sales GROUP_BY region COMPUTE SUM(amount) AS total INTO by_region
            STEP s2: FILTER by_region WHERE total > 100 INTO high_value
            STEP s3: SORT high_value BY total DESC INTO result
            OUTPUT result
        '''
        result = run(code, {"sales": [
            {"region": "North", "product": "A", "amount": 50},
            {"region": "North", "product": "B", "amount": 75},
            {"region": "South", "product": "A", "amount": 30},
            {"region": "East", "product": "C", "amount": 200},
        ]})
        assert len(result) == 2
        assert result[0]["region"] == "East"
        assert result[0]["total"] == 200


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_table(self) -> None:
        """Test operations on empty table."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            STEP s1: FILTER data WHERE id > 0 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": []})
        assert result == []

    def test_single_row(self) -> None:
        """Test operations on single row table."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[id: INT]
            STEP s1: LIMIT data COUNT 10 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"id": 1}]})
        assert len(result) == 1

    def test_null_values_in_operations(self) -> None:
        """Test handling of null values."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH safe => COALESCE(value, 0) INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"value": None}, {"value": 5}]})
        assert result[0]["safe"] == 0
        assert result[1]["safe"] == 5

    def test_special_characters_in_strings(self) -> None:
        """Test strings with special characters."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[text: STRING]
            STEP s1: MAP data WITH upper => UPPER(text) INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"text": "hello-world_test.123"}]})
        assert result[0]["upper"] == "HELLO-WORLD_TEST.123"

    def test_large_numbers(self) -> None:
        """Test with large numbers."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: INT]
            STEP s1: MAP data WITH doubled => value * 2 INTO result
            OUTPUT result
        '''
        result = run(code, {"data": [{"value": 10**15}]})
        assert result[0]["doubled"] == 2 * 10**15

    def test_decimal_precision(self) -> None:
        """Test decimal precision in calculations."""
        code = '''
        PIPELINE test:
            INPUT data: TABLE[value: DECIMAL]
            STEP s1: MAP data WITH result => ROUND(value / 3, 4) INTO output
            OUTPUT output
        '''
        result = run(code, {"data": [{"value": 10.0}]})
        assert abs(result[0]["result"] - 3.3333) < 0.0001
