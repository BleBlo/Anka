"""Tests for Control Flow features (SET, IF/ELSE, FOR_EACH, etc.)."""

import pytest

from anka.grammar.parser import Parser
from anka.runtime.interpreter import Interpreter


@pytest.fixture
def parser() -> Parser:
    """Create a parser instance."""
    return Parser()


@pytest.fixture
def interpreter() -> Interpreter:
    """Create an interpreter instance."""
    return Interpreter()


class TestSetStatement:
    """Tests for SET statement."""

    def test_set_number(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET with numeric value."""
        source = '''
        PIPELINE set_num_test:
            INPUT data: TABLE[x: INT]

            SET counter = 42

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("counter") == 42

    def test_set_decimal(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET with decimal value."""
        source = '''
        PIPELINE set_dec_test:
            INPUT data: TABLE[x: INT]

            SET rate = 3.14

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("rate") == 3.14

    def test_set_string(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET with string value."""
        source = '''
        PIPELINE set_str_test:
            INPUT data: TABLE[x: INT]

            SET name = "hello"

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("name") == "hello"

    def test_set_true(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET with true value."""
        source = '''
        PIPELINE set_bool_test:
            INPUT data: TABLE[x: INT]

            SET flag = true

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("flag") is True

    def test_set_false(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET with false value."""
        source = '''
        PIPELINE set_bool_test:
            INPUT data: TABLE[x: INT]

            SET flag = false

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("flag") is False

    def test_set_arithmetic(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET with arithmetic expression."""
        source = '''
        PIPELINE set_arith_test:
            INPUT data: TABLE[x: INT]

            SET result = 10 + 5 * 2

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == 20

    def test_set_with_step(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET mixed with STEP."""
        source = '''
        PIPELINE mixed_test:
            INPUT data: TABLE[x: INT]

            SET multiplier = 10

            STEP transform:
                MAP data
                WITH y => x * multiplier
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"x": 1}, {"x": 2}, {"x": 3}]})

        assert result is not None
        assert result[0]["y"] == 10
        assert result[1]["y"] == 20
        assert result[2]["y"] == 30

    def test_set_update_variable(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET can update existing variable."""
        source = '''
        PIPELINE update_test:
            INPUT data: TABLE[x: INT]

            SET counter = 1
            SET counter = 2

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("counter") == 2

    def test_set_from_variable(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SET from another variable."""
        source = '''
        PIPELINE copy_test:
            INPUT data: TABLE[x: INT]

            SET a = 100
            SET b = a

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("a") == 100
        assert interpreter.get_scalar("b") == 100

    def test_multiple_sets_with_steps(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test multiple SET statements interleaved with steps."""
        source = '''
        PIPELINE complex_test:
            INPUT data: TABLE[value: INT]

            SET offset = 10

            STEP add_offset:
                MAP data
                WITH adjusted => value + offset
                INTO with_offset

            SET scale = 2

            STEP scale_values:
                MAP with_offset
                WITH scaled => adjusted * scale
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert result[0]["adjusted"] == 15  # 5 + 10
        assert result[0]["scaled"] == 30    # 15 * 2

    def test_get_scalars(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test getting all scalar variables."""
        source = '''
        PIPELINE scalars_test:
            INPUT data: TABLE[x: INT]

            SET a = 1
            SET b = "two"
            SET c = true

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        scalars = interpreter.get_scalars()
        assert scalars == {"a": 1, "b": "two", "c": True}


class TestIfStatement:
    """Tests for IF/ELSE statement."""

    def test_if_true(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IF with true condition."""
        source = '''
        PIPELINE if_true_test:
            INPUT data: TABLE[x: INT]

            SET value = 10

            IF value > 5:
                SET result = "big"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "big"

    def test_if_false(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IF with false condition (no else)."""
        source = '''
        PIPELINE if_false_test:
            INPUT data: TABLE[x: INT]

            SET value = 3
            SET result = "default"

            IF value > 5:
                SET result = "big"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "default"

    def test_if_else_true_branch(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test IF/ELSE where condition is true."""
        source = '''
        PIPELINE if_else_test:
            INPUT data: TABLE[x: INT]

            SET value = 10

            IF value > 5:
                SET result = "big"
            ELSE:
                SET result = "small"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "big"

    def test_if_else_false_branch(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test IF/ELSE where condition is false."""
        source = '''
        PIPELINE if_else_test:
            INPUT data: TABLE[x: INT]

            SET value = 3

            IF value > 5:
                SET result = "big"
            ELSE:
                SET result = "small"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "small"

    def test_if_else_if(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IF/ELSE IF chain."""
        source = '''
        PIPELINE if_else_if_test:
            INPUT data: TABLE[x: INT]

            SET value = 5

            IF value > 10:
                SET result = "large"
            ELSE:
                IF value > 3:
                    SET result = "medium"
                ELSE:
                    SET result = "small"
                END
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "medium"

    def test_if_with_step(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IF containing STEP."""
        source = '''
        PIPELINE if_step_test:
            INPUT data: TABLE[value: INT]

            SET should_double = true

            IF should_double == true:
                STEP double_it:
                    MAP data
                    WITH doubled => value * 2
                    INTO result
            ELSE:
                STEP keep_it:
                    MAP data
                    WITH doubled => value
                    INTO result
            END

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert result[0]["doubled"] == 10

    def test_if_with_equality(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IF with equality comparison."""
        source = '''
        PIPELINE if_eq_test:
            INPUT data: TABLE[x: INT]

            SET status = "active"

            IF status == "active":
                SET result = 1
            ELSE:
                SET result = 0
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == 1

    def test_nested_if(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test nested IF statements."""
        source = '''
        PIPELINE nested_if_test:
            INPUT data: TABLE[x: INT]

            SET a = 10
            SET b = 5

            IF a > 5:
                IF b > 3:
                    SET result = "both"
                ELSE:
                    SET result = "a_only"
                END
            ELSE:
                SET result = "neither"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "both"

    def test_if_multiple_statements(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test IF with multiple statements in body."""
        source = '''
        PIPELINE if_multi_test:
            INPUT data: TABLE[x: INT]

            SET flag = true

            IF flag == true:
                SET a = 1
                SET b = 2
                SET c = 3
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("a") == 1
        assert interpreter.get_scalar("b") == 2
        assert interpreter.get_scalar("c") == 3


class TestForEachStatement:
    """Tests for FOR_EACH statement."""

    def test_for_each_counter(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test FOR_EACH to count items."""
        source = '''
        PIPELINE for_each_count_test:
            INPUT data: TABLE[value: INT]

            SET count = 0

            FOR_EACH row IN data:
                SET count = count + 1
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [
            {"value": 10},
            {"value": 20},
            {"value": 30}
        ]})

        assert interpreter.get_scalar("count") == 3

    def test_for_each_nested(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test nested FOR_EACH loops."""
        source = '''
        PIPELINE nested_for_each_test:
            INPUT outer: TABLE[x: INT]
            INPUT inner: TABLE[y: INT]

            SET count = 0

            FOR_EACH o IN outer:
                FOR_EACH i IN inner:
                    SET count = count + 1
                END
            END

            OUTPUT outer
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {
            "outer": [{"x": 1}, {"x": 2}],
            "inner": [{"y": 1}, {"y": 2}, {"y": 3}]
        })

        assert interpreter.get_scalar("count") == 6  # 2 * 3

    def test_for_each_with_step(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test FOR_EACH with STEP inside."""
        source = '''
        PIPELINE for_each_step_test:
            INPUT data: TABLE[value: INT]

            SET iterations = 0

            FOR_EACH row IN data:
                SET iterations = iterations + 1
            END

            STEP final:
                MAP data
                WITH count => iterations
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"value": 1},
            {"value": 2}
        ]})

        assert result is not None
        assert result[0]["count"] == 2
        assert result[1]["count"] == 2

    def test_for_each_set_last_value(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test FOR_EACH setting a value each iteration."""
        source = '''
        PIPELINE for_each_last_test:
            INPUT data: TABLE[value: INT]

            SET last_index = 0

            FOR_EACH row IN data:
                SET last_index = last_index + 1
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [
            {"value": 10},
            {"value": 20}
        ]})

        assert interpreter.get_scalar("last_index") == 2


class TestWhileStatement:
    """Tests for WHILE statement."""

    def test_while_countdown(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test WHILE loop with countdown."""
        source = '''
        PIPELINE while_countdown_test:
            INPUT data: TABLE[x: INT]

            SET counter = 5
            SET sum = 0

            WHILE counter > 0:
                SET sum = sum + counter
                SET counter = counter - 1
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("counter") == 0
        assert interpreter.get_scalar("sum") == 15  # 5+4+3+2+1

    def test_while_false_from_start(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test WHILE that never executes."""
        source = '''
        PIPELINE while_never_test:
            INPUT data: TABLE[x: INT]

            SET counter = 0
            SET executed = false

            WHILE counter > 0:
                SET executed = true
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("executed") is False

    def test_while_with_if(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test WHILE with IF inside."""
        source = '''
        PIPELINE while_if_test:
            INPUT data: TABLE[x: INT]

            SET n = 10
            SET even_count = 0

            WHILE n > 0:
                IF n > 5:
                    SET even_count = even_count + 1
                END
                SET n = n - 1
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("n") == 0
        assert interpreter.get_scalar("even_count") == 5  # 10,9,8,7,6 > 5

    def test_while_string_condition(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test WHILE with string comparison."""
        source = '''
        PIPELINE while_string_test:
            INPUT data: TABLE[x: INT]

            SET status = "running"
            SET iterations = 0

            WHILE status == "running":
                SET iterations = iterations + 1
                IF iterations > 3:
                    SET status = "done"
                END
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("status") == "done"
        assert interpreter.get_scalar("iterations") == 4

    def test_while_with_step(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test WHILE followed by STEP using loop result."""
        source = '''
        PIPELINE while_step_test:
            INPUT data: TABLE[value: INT]

            SET iterations = 0

            WHILE iterations < 3:
                SET iterations = iterations + 1
            END

            STEP add_count:
                MAP data
                WITH loop_count => iterations
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 1}]})

        assert result is not None
        assert result[0]["loop_count"] == 3


class TestTryStatement:
    """Tests for TRY/ON_ERROR statement."""

    def test_try_success(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test TRY with successful execution."""
        source = '''
        PIPELINE try_success_test:
            INPUT data: TABLE[x: INT]

            SET result = "initial"

            TRY:
                SET result = "success"
            ON_ERROR:
                SET result = "error"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "success"

    def test_try_with_error(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test TRY with error triggering ON_ERROR."""
        source = '''
        PIPELINE try_error_test:
            INPUT data: TABLE[x: INT]

            SET result = "initial"

            TRY:
                STEP bad_filter:
                    FILTER nonexistent
                    WHERE x > 0
                    INTO filtered
                SET result = "success"
            ON_ERROR:
                SET result = "error_handled"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "error_handled"

    def test_try_with_multiple_statements(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test TRY with multiple statements in body."""
        source = '''
        PIPELINE try_multi_test:
            INPUT data: TABLE[x: INT]

            SET a = 0
            SET b = 0
            SET c = 0

            TRY:
                SET a = 1
                SET b = 2
                SET c = 3
            ON_ERROR:
                SET a = 99
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("a") == 1
        assert interpreter.get_scalar("b") == 2
        assert interpreter.get_scalar("c") == 3

    def test_try_with_step_success(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test TRY containing successful STEP."""
        source = '''
        PIPELINE try_step_test:
            INPUT data: TABLE[value: INT]

            SET status = "pending"

            TRY:
                STEP transform:
                    MAP data
                    WITH doubled => value * 2
                    INTO result
                SET status = "success"
            ON_ERROR:
                SET status = "failed"
            END

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert result[0]["doubled"] == 10
        assert interpreter.get_scalar("status") == "success"

    def test_try_error_in_step(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test TRY with error in STEP operation."""
        source = '''
        PIPELINE try_step_error_test:
            INPUT data: TABLE[x: INT]

            SET status = "pending"

            TRY:
                STEP bad_select:
                    SELECT nonexistent_column
                    FROM data
                    INTO result
                SET status = "success"
            ON_ERROR:
                SET status = "recovered"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("status") == "recovered"

    def test_try_with_if_inside(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test TRY with IF statement inside."""
        source = '''
        PIPELINE try_if_test:
            INPUT data: TABLE[x: INT]

            SET value = 10
            SET result = "none"

            TRY:
                IF value > 5:
                    SET result = "big"
                ELSE:
                    SET result = "small"
                END
            ON_ERROR:
                SET result = "error"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "big"

    def test_try_nested(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test nested TRY statements."""
        source = '''
        PIPELINE try_nested_test:
            INPUT data: TABLE[x: INT]

            SET outer_result = "pending"
            SET inner_result = "pending"

            TRY:
                SET outer_result = "started"
                TRY:
                    STEP bad_op:
                        FILTER missing_table
                        WHERE x > 0
                        INTO filtered
                    SET inner_result = "success"
                ON_ERROR:
                    SET inner_result = "inner_error"
                END
                SET outer_result = "completed"
            ON_ERROR:
                SET outer_result = "outer_error"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("outer_result") == "completed"
        assert interpreter.get_scalar("inner_result") == "inner_error"

    def test_try_with_for_each(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test TRY with FOR_EACH inside."""
        source = '''
        PIPELINE try_foreach_test:
            INPUT data: TABLE[x: INT]

            SET count = 0
            SET status = "pending"

            TRY:
                FOR_EACH row IN data:
                    SET count = count + 1
                END
                SET status = "done"
            ON_ERROR:
                SET status = "failed"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}, {"x": 2}, {"x": 3}]})

        assert interpreter.get_scalar("count") == 3
        assert interpreter.get_scalar("status") == "done"

    def test_try_with_while(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test TRY with WHILE inside."""
        source = '''
        PIPELINE try_while_test:
            INPUT data: TABLE[x: INT]

            SET counter = 3
            SET sum = 0
            SET status = "pending"

            TRY:
                WHILE counter > 0:
                    SET sum = sum + counter
                    SET counter = counter - 1
                END
                SET status = "done"
            ON_ERROR:
                SET status = "failed"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("sum") == 6  # 3+2+1
        assert interpreter.get_scalar("counter") == 0
        assert interpreter.get_scalar("status") == "done"

    def test_try_error_body_with_step(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test ON_ERROR body containing STEP."""
        source = '''
        PIPELINE try_error_step_test:
            INPUT data: TABLE[value: INT]

            SET status = "pending"

            TRY:
                STEP bad_op:
                    FILTER missing
                    WHERE value > 0
                    INTO filtered
                SET status = "success"
            ON_ERROR:
                STEP default_transform:
                    MAP data
                    WITH default_val => 0
                    INTO result
                SET status = "recovered"
            END

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert result[0]["default_val"] == 0
        assert interpreter.get_scalar("status") == "recovered"


class TestMatchStatement:
    """Tests for MATCH pattern matching statement."""

    def test_match_string_first_case(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with string value matching first case."""
        source = '''
        PIPELINE match_string_test:
            INPUT data: TABLE[x: INT]

            SET status = "pending"

            MATCH status:
                CASE "pending":
                    SET result = "awaiting"
                CASE "active":
                    SET result = "in_progress"
                CASE "done":
                    SET result = "completed"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "awaiting"

    def test_match_string_middle_case(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with string value matching middle case."""
        source = '''
        PIPELINE match_middle_test:
            INPUT data: TABLE[x: INT]

            SET status = "active"

            MATCH status:
                CASE "pending":
                    SET result = "awaiting"
                CASE "active":
                    SET result = "in_progress"
                CASE "done":
                    SET result = "completed"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "in_progress"

    def test_match_with_default(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with DEFAULT case."""
        source = '''
        PIPELINE match_default_test:
            INPUT data: TABLE[x: INT]

            SET status = "unknown_status"

            MATCH status:
                CASE "pending":
                    SET result = "awaiting"
                CASE "active":
                    SET result = "in_progress"
                DEFAULT:
                    SET result = "unknown"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "unknown"

    def test_match_no_default_no_match(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with no matching case and no default."""
        source = '''
        PIPELINE match_no_default_test:
            INPUT data: TABLE[x: INT]

            SET status = "other"
            SET result = "original"

            MATCH status:
                CASE "pending":
                    SET result = "awaiting"
                CASE "active":
                    SET result = "in_progress"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        # Result should be unchanged since no case matched
        assert interpreter.get_scalar("result") == "original"

    def test_match_number(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test MATCH with numeric values."""
        source = '''
        PIPELINE match_number_test:
            INPUT data: TABLE[x: INT]

            SET code = 2

            MATCH code:
                CASE 1:
                    SET result = "one"
                CASE 2:
                    SET result = "two"
                CASE 3:
                    SET result = "three"
                DEFAULT:
                    SET result = "other"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "two"

    def test_match_boolean(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test MATCH with boolean values."""
        source = '''
        PIPELINE match_bool_test:
            INPUT data: TABLE[x: INT]

            SET flag = true

            MATCH flag:
                CASE true:
                    SET result = "yes"
                CASE false:
                    SET result = "no"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "yes"

    def test_match_multiple_statements_in_case(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with multiple statements in a case."""
        source = '''
        PIPELINE match_multi_stmt_test:
            INPUT data: TABLE[x: INT]

            SET status = "active"

            MATCH status:
                CASE "active":
                    SET a = 1
                    SET b = 2
                    SET c = 3
                DEFAULT:
                    SET a = 0
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("a") == 1
        assert interpreter.get_scalar("b") == 2
        assert interpreter.get_scalar("c") == 3

    def test_match_with_step_in_case(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with STEP inside a case."""
        source = '''
        PIPELINE match_step_test:
            INPUT data: TABLE[value: INT]

            SET mode = "double"

            MATCH mode:
                CASE "double":
                    STEP double_it:
                        MAP data
                        WITH result => value * 2
                        INTO output
                CASE "triple":
                    STEP triple_it:
                        MAP data
                        WITH result => value * 3
                        INTO output
                DEFAULT:
                    STEP keep_it:
                        MAP data
                        WITH result => value
                        INTO output
            END

            OUTPUT output
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert result[0]["result"] == 10

    def test_match_nested_in_if(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH nested inside IF statement."""
        source = '''
        PIPELINE match_in_if_test:
            INPUT data: TABLE[x: INT]

            SET check = true
            SET status = "pending"
            SET result = "none"

            IF check == true:
                MATCH status:
                    CASE "pending":
                        SET result = "waiting"
                    DEFAULT:
                        SET result = "other"
                END
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "waiting"

    def test_match_with_if_inside_case(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test MATCH with IF statement inside a case."""
        source = '''
        PIPELINE match_with_if_test:
            INPUT data: TABLE[x: INT]

            SET status = "active"
            SET priority = 10

            MATCH status:
                CASE "active":
                    IF priority > 5:
                        SET result = "high_priority_active"
                    ELSE:
                        SET result = "low_priority_active"
                    END
                DEFAULT:
                    SET result = "inactive"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "high_priority_active"

    def test_match_decimal(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test MATCH with decimal values."""
        source = '''
        PIPELINE match_decimal_test:
            INPUT data: TABLE[x: INT]

            SET rate = 1.5

            MATCH rate:
                CASE 1.0:
                    SET result = "standard"
                CASE 1.5:
                    SET result = "premium"
                CASE 2.0:
                    SET result = "deluxe"
                DEFAULT:
                    SET result = "custom"
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "premium"


class TestAssertStatement:
    """Tests for ASSERT statement."""

    def test_assert_passes(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ASSERT with true condition."""
        source = '''
        PIPELINE assert_pass_test:
            INPUT data: TABLE[x: INT]

            SET value = 10

            ASSERT value > 5

            SET result = "passed"

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "passed"

    def test_assert_fails(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ASSERT with false condition raises error."""
        from anka.runtime.interpreter import AssertionError as AnkaAssertionError

        source = '''
        PIPELINE assert_fail_test:
            INPUT data: TABLE[x: INT]

            SET value = 3

            ASSERT value > 5

            OUTPUT data
        '''
        ast = parser.parse(source)

        with pytest.raises(AnkaAssertionError):
            interpreter.execute(ast, {"data": [{"x": 1}]})

    def test_assert_with_message(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test ASSERT with custom message."""
        from anka.runtime.interpreter import AssertionError as AnkaAssertionError

        source = '''
        PIPELINE assert_msg_test:
            INPUT data: TABLE[x: INT]

            SET value = 0

            ASSERT value > 0 MESSAGE "Value must be positive"

            OUTPUT data
        '''
        ast = parser.parse(source)

        with pytest.raises(AnkaAssertionError) as exc_info:
            interpreter.execute(ast, {"data": [{"x": 1}]})

        assert "Value must be positive" in str(exc_info.value)

    def test_assert_equality(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ASSERT with equality condition."""
        source = '''
        PIPELINE assert_eq_test:
            INPUT data: TABLE[x: INT]

            SET status = "active"

            ASSERT status == "active"

            SET result = "ok"

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "ok"


class TestReturnStatement:
    """Tests for RETURN statement."""

    def test_return_early_exit(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test RETURN exits pipeline early."""
        source = '''
        PIPELINE return_early_test:
            INPUT data: TABLE[x: INT]

            SET result = "before"

            RETURN

            SET result = "after"

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        # Result should be "before" since RETURN exits before the second SET
        assert interpreter.get_scalar("result") == "before"

    def test_return_with_value(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test RETURN with a value."""
        source = '''
        PIPELINE return_value_test:
            INPUT data: TABLE[value: INT]

            STEP transform:
                MAP data
                WITH doubled => value * 2
                INTO result

            RETURN result

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert result[0]["doubled"] == 10

    def test_return_in_if(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test RETURN inside IF statement."""
        source = '''
        PIPELINE return_if_test:
            INPUT data: TABLE[x: INT]

            SET value = 10
            SET result = "initial"

            IF value > 5:
                SET result = "big"
                RETURN
            END

            SET result = "should_not_reach"

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("result") == "big"


class TestBreakStatement:
    """Tests for BREAK statement."""

    def test_break_in_for_each(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test BREAK exits FOR_EACH loop."""
        source = '''
        PIPELINE break_foreach_test:
            INPUT data: TABLE[value: INT]

            SET count = 0

            FOR_EACH row IN data:
                SET count = count + 1
                IF count == 2:
                    BREAK
                END
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [
            {"value": 1}, {"value": 2}, {"value": 3}, {"value": 4}, {"value": 5}
        ]})

        assert interpreter.get_scalar("count") == 2

    def test_break_in_while(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test BREAK exits WHILE loop."""
        source = '''
        PIPELINE break_while_test:
            INPUT data: TABLE[x: INT]

            SET counter = 0
            SET sum = 0

            WHILE counter < 100:
                SET counter = counter + 1
                SET sum = sum + counter
                IF counter == 5:
                    BREAK
                END
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("counter") == 5
        assert interpreter.get_scalar("sum") == 15  # 1+2+3+4+5

    def test_break_nested_loop(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test BREAK only exits innermost loop."""
        source = '''
        PIPELINE break_nested_test:
            INPUT outer: TABLE[x: INT]
            INPUT inner: TABLE[y: INT]

            SET outer_count = 0
            SET inner_count = 0

            FOR_EACH o IN outer:
                SET outer_count = outer_count + 1
                FOR_EACH i IN inner:
                    SET inner_count = inner_count + 1
                    IF inner_count == 2:
                        BREAK
                    END
                END
            END

            OUTPUT outer
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {
            "outer": [{"x": 1}, {"x": 2}],
            "inner": [{"y": 1}, {"y": 2}, {"y": 3}]
        })

        assert interpreter.get_scalar("outer_count") == 2
        # First outer: inner_count goes 1, 2 (break when ==2)
        # Second outer: inner_count is 2, goes to 3, 4, 5 (no break since never ==2 again)
        # Total: 1, 2(break), 3, 4, 5 = 5
        assert interpreter.get_scalar("inner_count") == 5


class TestContinueStatement:
    """Tests for CONTINUE statement."""

    def test_continue_in_for_each(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test CONTINUE skips to next iteration in FOR_EACH."""
        source = '''
        PIPELINE continue_foreach_test:
            INPUT data: TABLE[value: INT]

            SET sum = 0
            SET count = 0

            FOR_EACH row IN data:
                SET count = count + 1
                IF count == 2:
                    CONTINUE
                END
                SET sum = sum + count
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [
            {"value": 1}, {"value": 2}, {"value": 3}
        ]})

        # sum = 1 + 3 = 4 (skipped count 2)
        assert interpreter.get_scalar("sum") == 4
        assert interpreter.get_scalar("count") == 3

    def test_continue_in_while(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test CONTINUE skips to next iteration in WHILE."""
        source = '''
        PIPELINE continue_while_test:
            INPUT data: TABLE[x: INT]

            SET counter = 0
            SET sum = 0

            WHILE counter < 5:
                SET counter = counter + 1
                IF counter == 3:
                    CONTINUE
                END
                SET sum = sum + counter
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert interpreter.get_scalar("counter") == 5
        # sum = 1 + 2 + 4 + 5 = 12 (skipped 3)
        assert interpreter.get_scalar("sum") == 12

    def test_continue_early_in_body(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test CONTINUE at start of loop body."""
        source = '''
        PIPELINE continue_early_test:
            INPUT data: TABLE[value: INT]

            SET count = 0
            SET processed = 0

            FOR_EACH row IN data:
                SET count = count + 1
                CONTINUE
                SET processed = processed + 1
            END

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [
            {"value": 1}, {"value": 2}, {"value": 3}
        ]})

        assert interpreter.get_scalar("count") == 3
        assert interpreter.get_scalar("processed") == 0


class TestAppendStatement:
    """Tests for APPEND statement."""

    def test_append_to_new_collection(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND creates new collection if target doesn't exist."""
        source = '''
        PIPELINE append_new_test:
            INPUT data: TABLE[value: INT]

            APPEND data TO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 1}, {"value": 2}]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["value"] == 1
        assert result[1]["value"] == 2

    def test_append_to_existing_collection(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND adds to existing collection."""
        source = '''
        PIPELINE append_existing_test:
            INPUT first: TABLE[value: INT]
            INPUT second: TABLE[value: INT]

            APPEND first TO result
            APPEND second TO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {
            "first": [{"value": 1}],
            "second": [{"value": 2}]
        })

        assert result is not None
        assert len(result) == 2
        assert result[0]["value"] == 1
        assert result[1]["value"] == 2

    def test_append_in_for_each(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND inside FOR_EACH loop."""
        source = '''
        PIPELINE append_loop_test:
            INPUT data: TABLE[value: INT]

            SET count = 0

            FOR_EACH row IN data:
                SET count = count + 1
                APPEND data TO collected
            END

            OUTPUT collected
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 10}, {"value": 20}]})

        # data has 2 rows, loop runs twice, each time appends all 2 rows
        # So collected has 4 items total
        assert result is not None
        assert len(result) == 4

    def test_append_with_filter_result(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND after FILTER operation."""
        source = '''
        PIPELINE append_filter_test:
            INPUT data: TABLE[value: INT]

            STEP filter_big:
                FILTER data
                WHERE value > 5
                INTO big_values

            STEP filter_small:
                FILTER data
                WHERE value <= 5
                INTO small_values

            APPEND big_values TO all_sorted
            APPEND small_values TO all_sorted

            OUTPUT all_sorted
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"value": 3}, {"value": 7}, {"value": 2}, {"value": 9}
        ]})

        assert result is not None
        assert len(result) == 4
        # big values first: 7, 9
        # small values second: 3, 2
        assert result[0]["value"] == 7
        assert result[1]["value"] == 9
        assert result[2]["value"] == 3
        assert result[3]["value"] == 2

    def test_append_multiple_times(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND multiple times to same target."""
        source = '''
        PIPELINE append_multi_test:
            INPUT a: TABLE[x: INT]
            INPUT b: TABLE[x: INT]
            INPUT c: TABLE[x: INT]

            APPEND a TO combined
            APPEND b TO combined
            APPEND c TO combined

            OUTPUT combined
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {
            "a": [{"x": 1}],
            "b": [{"x": 2}],
            "c": [{"x": 3}]
        })

        assert result is not None
        assert len(result) == 3
        assert result[0]["x"] == 1
        assert result[1]["x"] == 2
        assert result[2]["x"] == 3

    def test_append_in_if(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND inside IF statement."""
        source = '''
        PIPELINE append_if_test:
            INPUT data: TABLE[value: INT]

            SET condition = true

            IF condition == true:
                APPEND data TO result
            ELSE:
                STEP empty:
                    FILTER data
                    WHERE value < 0
                    INTO result
            END

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["value"] == 5

    def test_append_with_map_result(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test APPEND with MAP operation result."""
        source = '''
        PIPELINE append_map_test:
            INPUT data: TABLE[value: INT]

            STEP transform:
                MAP data
                WITH doubled => value * 2
                INTO transformed

            APPEND transformed TO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [{"value": 5}]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["doubled"] == 10
