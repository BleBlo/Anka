"""Tests for String operations (functions and checks)."""

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


class TestStringFunctions:
    """Tests for string functions in MAP expressions."""

    def test_upper(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test UPPER function."""
        source = '''
        PIPELINE upper_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH upper_name => UPPER(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "alice"},
            {"name": "Bob"},
            {"name": "CHARLIE"},
        ]})

        assert result is not None
        assert result[0]["upper_name"] == "ALICE"
        assert result[1]["upper_name"] == "BOB"
        assert result[2]["upper_name"] == "CHARLIE"

    def test_lower(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test LOWER function."""
        source = '''
        PIPELINE lower_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH lower_name => LOWER(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "ALICE"},
            {"name": "Bob"},
            {"name": "charlie"},
        ]})

        assert result is not None
        assert result[0]["lower_name"] == "alice"
        assert result[1]["lower_name"] == "bob"
        assert result[2]["lower_name"] == "charlie"

    def test_trim(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test TRIM function."""
        source = '''
        PIPELINE trim_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH trimmed => TRIM(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "  alice  "},
            {"name": "bob"},
            {"name": "\tcharlie\n"},
        ]})

        assert result is not None
        assert result[0]["trimmed"] == "alice"
        assert result[1]["trimmed"] == "bob"
        assert result[2]["trimmed"] == "charlie"

    def test_ltrim(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test LTRIM function."""
        source = '''
        PIPELINE ltrim_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH trimmed => LTRIM(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "  alice  "},
        ]})

        assert result is not None
        assert result[0]["trimmed"] == "alice  "

    def test_rtrim(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test RTRIM function."""
        source = '''
        PIPELINE rtrim_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH trimmed => RTRIM(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "  alice  "},
        ]})

        assert result is not None
        assert result[0]["trimmed"] == "  alice"

    def test_length(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test LENGTH function."""
        source = '''
        PIPELINE length_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH len => LENGTH(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "alice"},
            {"name": ""},
            {"name": "hello world"},
        ]})

        assert result is not None
        assert result[0]["len"] == 5
        assert result[1]["len"] == 0
        assert result[2]["len"] == 11

    def test_reverse(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test REVERSE function."""
        source = '''
        PIPELINE reverse_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH reversed => REVERSE(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "hello"},
            {"name": "racecar"},
        ]})

        assert result is not None
        assert result[0]["reversed"] == "olleh"
        assert result[1]["reversed"] == "racecar"

    def test_substring(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test SUBSTRING function."""
        source = '''
        PIPELINE substring_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH sub => SUBSTRING(name, 0, 3)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "hello world"},
        ]})

        assert result is not None
        assert result[0]["sub"] == "hel"

    def test_left(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test LEFT function."""
        source = '''
        PIPELINE left_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH prefix => LEFT(name, 3)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "hello"},
        ]})

        assert result is not None
        assert result[0]["prefix"] == "hel"

    def test_right(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test RIGHT function."""
        source = '''
        PIPELINE right_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH suffix => RIGHT(name, 3)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "hello"},
        ]})

        assert result is not None
        assert result[0]["suffix"] == "llo"

    def test_index_of(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test INDEX_OF function."""
        source = '''
        PIPELINE index_of_test:
            INPUT data: TABLE[text: STRING, search: STRING]

            STEP transform:
                MAP data
                WITH pos => INDEX_OF(text, search)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"text": "hello world", "search": "world"},
            {"text": "hello world", "search": "xyz"},
        ]})

        assert result is not None
        assert result[0]["pos"] == 6
        assert result[1]["pos"] == -1

    def test_replace(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test REPLACE function (first occurrence only)."""
        source = '''
        PIPELINE replace_test:
            INPUT data: TABLE[text: STRING, old_val: STRING, new_val: STRING]

            STEP transform:
                MAP data
                WITH replaced => REPLACE(text, old_val, new_val)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"text": "hello hello", "old_val": "hello", "new_val": "hi"},
        ]})

        assert result is not None
        assert result[0]["replaced"] == "hi hello"

    def test_replace_all(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test REPLACE_ALL function."""
        source = '''
        PIPELINE replace_all_test:
            INPUT data: TABLE[text: STRING, old_val: STRING, new_val: STRING]

            STEP transform:
                MAP data
                WITH replaced => REPLACE_ALL(text, old_val, new_val)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"text": "hello hello", "old_val": "hello", "new_val": "hi"},
        ]})

        assert result is not None
        assert result[0]["replaced"] == "hi hi"

    def test_pad_left(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test PAD_LEFT function."""
        source = '''
        PIPELINE pad_left_test:
            INPUT data: TABLE[num: STRING, char: STRING]

            STEP transform:
                MAP data
                WITH padded => PAD_LEFT(num, 5, char)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"num": "42", "char": "0"},
        ]})

        assert result is not None
        assert result[0]["padded"] == "00042"

    def test_pad_right(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test PAD_RIGHT function."""
        source = '''
        PIPELINE pad_right_test:
            INPUT data: TABLE[name: STRING, char: STRING]

            STEP transform:
                MAP data
                WITH padded => PAD_RIGHT(name, 10, char)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "Alice", "char": "."},
        ]})

        assert result is not None
        assert result[0]["padded"] == "Alice....."

    def test_repeat(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test REPEAT function."""
        source = '''
        PIPELINE repeat_test:
            INPUT data: TABLE[text: STRING]

            STEP transform:
                MAP data
                WITH repeated => REPEAT(text, 3)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"text": "ab"},
        ]})

        assert result is not None
        assert result[0]["repeated"] == "ababab"

    def test_concat(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test CONCAT function."""
        source = '''
        PIPELINE concat_test:
            INPUT data: TABLE[first: STRING, last: STRING]

            STEP transform:
                MAP data
                WITH full_name => CONCAT(first, " ", last)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"first": "John", "last": "Doe"},
        ]})

        assert result is not None
        assert result[0]["full_name"] == "John Doe"

    def test_nested_string_functions(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test nested string functions like UPPER(TRIM(name))."""
        source = '''
        PIPELINE nested_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH clean_name => UPPER(TRIM(name))
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "  alice  "},
        ]})

        assert result is not None
        assert result[0]["clean_name"] == "ALICE"

    def test_null_handling(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test string functions with null values."""
        source = '''
        PIPELINE null_test:
            INPUT data: TABLE[name: STRING]

            STEP transform:
                MAP data
                WITH upper_name => UPPER(name)
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": None},
        ]})

        assert result is not None
        assert result[0]["upper_name"] == ""


class TestStringChecks:
    """Tests for string checks in FILTER WHERE clauses."""

    def test_contains(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test CONTAINS check."""
        source = '''
        PIPELINE contains_test:
            INPUT data: TABLE[name: STRING]

            STEP filter:
                FILTER data
                WHERE CONTAINS(name, "li")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"},
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Charlie"

    def test_starts_with(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test STARTS_WITH check."""
        source = '''
        PIPELINE starts_with_test:
            INPUT data: TABLE[name: STRING]

            STEP filter:
                FILTER data
                WHERE STARTS_WITH(name, "Al")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "Alice"},
            {"name": "Albert"},
            {"name": "Bob"},
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Albert"

    def test_ends_with(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test ENDS_WITH check."""
        source = '''
        PIPELINE ends_with_test:
            INPUT data: TABLE[email: STRING]

            STEP filter:
                FILTER data
                WHERE ENDS_WITH(email, ".com")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"email": "alice@example.com"},
            {"email": "bob@example.org"},
            {"email": "charlie@example.com"},
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["email"] == "alice@example.com"
        assert result[1]["email"] == "charlie@example.com"

    def test_matches(self, parser: Parser, interpreter: Interpreter) -> None:
        """Test MATCHES check with regex."""
        source = '''
        PIPELINE matches_test:
            INPUT data: TABLE[phone: STRING]

            STEP filter:
                FILTER data
                WHERE MATCHES(phone, "[0-9]{3}-[0-9]{4}")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"phone": "555-1234"},
            {"phone": "abc-defg"},
            {"phone": "123-5678"},
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["phone"] == "555-1234"
        assert result[1]["phone"] == "123-5678"

    def test_string_check_with_null(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test string checks with null values."""
        source = '''
        PIPELINE null_check_test:
            INPUT data: TABLE[name: STRING]

            STEP filter:
                FILTER data
                WHERE CONTAINS(name, "li")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "Alice"},
            {"name": None},
            {"name": "Charlie"},
        ]})

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Charlie"

    def test_string_check_combined_with_and(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test string check combined with AND."""
        source = '''
        PIPELINE combined_test:
            INPUT data: TABLE[name: STRING, age: INT]

            STEP filter:
                FILTER data
                WHERE STARTS_WITH(name, "A") AND age > 20
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "Alice", "age": 25},
            {"name": "Albert", "age": 18},
            {"name": "Bob", "age": 30},
        ]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_string_check_with_not(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test NOT with string check."""
        source = '''
        PIPELINE not_test:
            INPUT data: TABLE[name: STRING]

            STEP filter:
                FILTER data
                WHERE NOT CONTAINS(name, "li")
                INTO result

            OUTPUT result
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"data": [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"},
        ]})

        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "Bob"
