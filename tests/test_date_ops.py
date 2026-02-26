"""Tests for Date/Time operations (functions and checks)."""

from datetime import datetime

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


class TestDateFunctions:
    """Tests for date functions in MAP expressions."""

    def test_year(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test YEAR function."""
        source = '''
        PIPELINE year_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH year => YEAR(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},
            {"order_date": "2023-12-01"},
        ]})

        assert result is not None
        assert result[0]["year"] == 2024
        assert result[1]["year"] == 2023

    def test_month(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test MONTH function."""
        source = '''
        PIPELINE month_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH month => MONTH(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},
            {"order_date": "2024-12-01"},
        ]})

        assert result is not None
        assert result[0]["month"] == 3
        assert result[1]["month"] == 12

    def test_day(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test DAY function."""
        source = '''
        PIPELINE day_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH day => DAY(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},
            {"order_date": "2024-03-01"},
        ]})

        assert result is not None
        assert result[0]["day"] == 15
        assert result[1]["day"] == 1

    def test_hour_minute_second(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test HOUR, MINUTE, SECOND functions."""
        source = '''
        PIPELINE time_test:
            INPUT data: TABLE[timestamp: STRING]

            STEP get_hour:
                MAP data
                WITH hour => HOUR(timestamp)
                INTO with_hour

            STEP get_minute:
                MAP with_hour
                WITH minute => MINUTE(timestamp)
                INTO with_minute

            STEP get_second:
                MAP with_minute
                WITH second => SECOND(timestamp)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"timestamp": "2024-03-15 14:30:45"},
        ]})

        assert result is not None
        assert result[0]["hour"] == 14
        assert result[0]["minute"] == 30
        assert result[0]["second"] == 45

    def test_day_of_week(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test DAY_OF_WEEK function."""
        source = '''
        PIPELINE dow_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH dow => DAY_OF_WEEK(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        # 2024-03-15 is a Friday (5)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},
        ]})

        assert result is not None
        assert result[0]["dow"] == 5  # Friday

    def test_week_of_year(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test WEEK_OF_YEAR function."""
        source = '''
        PIPELINE woy_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH week => WEEK_OF_YEAR(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},
        ]})

        assert result is not None
        assert result[0]["week"] == 11  # Week 11 of 2024

    def test_add_days(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ADD_DAYS function."""
        source = '''
        PIPELINE add_days_test:
            INPUT data: TABLE[start_date: STRING, days_to_add: INT]

            STEP transform:
                MAP data
                WITH end_date => ADD_DAYS(start_date, days_to_add)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"start_date": "2024-03-15", "days_to_add": 10},
        ]})

        assert result is not None
        end_date = result[0]["end_date"]
        assert isinstance(end_date, datetime)
        assert end_date.year == 2024
        assert end_date.month == 3
        assert end_date.day == 25

    def test_add_months(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ADD_MONTHS function."""
        source = '''
        PIPELINE add_months_test:
            INPUT data: TABLE[start_date: STRING]

            STEP transform:
                MAP data
                WITH end_date => ADD_MONTHS(start_date, 3)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"start_date": "2024-03-15"},
        ]})

        assert result is not None
        end_date = result[0]["end_date"]
        assert isinstance(end_date, datetime)
        assert end_date.year == 2024
        assert end_date.month == 6
        assert end_date.day == 15

    def test_add_years(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ADD_YEARS function."""
        source = '''
        PIPELINE add_years_test:
            INPUT data: TABLE[start_date: STRING]

            STEP transform:
                MAP data
                WITH end_date => ADD_YEARS(start_date, 2)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"start_date": "2024-03-15"},
        ]})

        assert result is not None
        end_date = result[0]["end_date"]
        assert isinstance(end_date, datetime)
        assert end_date.year == 2026
        assert end_date.month == 3
        assert end_date.day == 15

    def test_add_hours(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ADD_HOURS function."""
        source = '''
        PIPELINE add_hours_test:
            INPUT data: TABLE[timestamp: STRING]

            STEP transform:
                MAP data
                WITH later => ADD_HOURS(timestamp, 5)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"timestamp": "2024-03-15 10:00:00"},
        ]})

        assert result is not None
        later = result[0]["later"]
        assert isinstance(later, datetime)
        assert later.hour == 15

    def test_diff_days(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test DIFF_DAYS function."""
        source = '''
        PIPELINE diff_days_test:
            INPUT data: TABLE[date1: STRING, date2: STRING]

            STEP transform:
                MAP data
                WITH days_diff => DIFF_DAYS(date1, date2)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"date1": "2024-03-25", "date2": "2024-03-15"},
        ]})

        assert result is not None
        assert result[0]["days_diff"] == 10

    def test_parse_date(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test PARSE_DATE function."""
        source = '''
        PIPELINE parse_date_test:
            INPUT data: TABLE[date_str: STRING]

            STEP transform:
                MAP data
                WITH parsed => PARSE_DATE(date_str, "YYYY-MM-DD")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"date_str": "2024-03-15"},
        ]})

        assert result is not None
        parsed = result[0]["parsed"]
        assert isinstance(parsed, datetime)
        assert parsed.year == 2024
        assert parsed.month == 3
        assert parsed.day == 15

    def test_format_date(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test FORMAT_DATE function."""
        source = '''
        PIPELINE format_date_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH formatted => FORMAT_DATE(order_date, "DD/MM/YYYY")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},
        ]})

        assert result is not None
        assert result[0]["formatted"] == "15/03/2024"

    def test_null_handling(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test date functions with null values."""
        source = '''
        PIPELINE null_test:
            INPUT data: TABLE[order_date: STRING]

            STEP transform:
                MAP data
                WITH year => YEAR(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": None},
        ]})

        assert result is not None
        assert result[0]["year"] is None


class TestDateChecks:
    """Tests for date checks in FILTER WHERE clauses."""

    def test_is_before(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IS_BEFORE check."""
        source = '''
        PIPELINE is_before_test:
            INPUT data: TABLE[order_date: STRING, cutoff: STRING]

            STEP filter:
                FILTER data
                WHERE IS_BEFORE(order_date, cutoff)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-10", "cutoff": "2024-03-15"},
            {"order_date": "2024-03-20", "cutoff": "2024-03-15"},
            {"order_date": "2024-03-15", "cutoff": "2024-03-15"},
        ]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["order_date"] == "2024-03-10"

    def test_is_after(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IS_AFTER check."""
        source = '''
        PIPELINE is_after_test:
            INPUT data: TABLE[order_date: STRING, cutoff: STRING]

            STEP filter:
                FILTER data
                WHERE IS_AFTER(order_date, cutoff)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-10", "cutoff": "2024-03-15"},
            {"order_date": "2024-03-20", "cutoff": "2024-03-15"},
            {"order_date": "2024-03-15", "cutoff": "2024-03-15"},
        ]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["order_date"] == "2024-03-20"

    def test_is_weekend(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test IS_WEEKEND check."""
        source = '''
        PIPELINE is_weekend_test:
            INPUT data: TABLE[order_date: STRING]

            STEP filter:
                FILTER data
                WHERE IS_WEEKEND(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        # 2024-03-16 is Saturday, 2024-03-15 is Friday
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},  # Friday
            {"order_date": "2024-03-16"},  # Saturday
            {"order_date": "2024-03-17"},  # Sunday
            {"order_date": "2024-03-18"},  # Monday
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["order_date"] == "2024-03-16"
        assert result[1]["order_date"] == "2024-03-17"

    def test_date_check_with_null(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test date checks with null values."""
        source = '''
        PIPELINE null_check_test:
            INPUT data: TABLE[order_date: STRING]

            STEP filter:
                FILTER data
                WHERE IS_WEEKEND(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-16"},  # Saturday
            {"order_date": None},
        ]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["order_date"] == "2024-03-16"

    def test_date_check_combined_with_and(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test date check combined with AND."""
        source = '''
        PIPELINE combined_test:
            INPUT data: TABLE[order_date: STRING, amount: INT]

            STEP filter:
                FILTER data
                WHERE IS_WEEKEND(order_date) AND amount > 100
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-16", "amount": 150},  # Saturday, > 100
            {"order_date": "2024-03-16", "amount": 50},   # Saturday, < 100
            {"order_date": "2024-03-15", "amount": 200},  # Friday, > 100
        ]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["amount"] == 150

    def test_not_is_weekend(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test NOT with IS_WEEKEND."""
        source = '''
        PIPELINE not_weekend_test:
            INPUT data: TABLE[order_date: STRING]

            STEP filter:
                FILTER data
                WHERE NOT IS_WEEKEND(order_date)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"order_date": "2024-03-15"},  # Friday
            {"order_date": "2024-03-16"},  # Saturday
            {"order_date": "2024-03-18"},  # Monday
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["order_date"] == "2024-03-15"
        assert result[1]["order_date"] == "2024-03-18"
