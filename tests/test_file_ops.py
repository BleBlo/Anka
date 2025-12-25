"""Tests for File I/O operations (READ, WRITE)."""

import json
from pathlib import Path

import pytest

from anka.grammar.parser import Parser
from anka.runtime.interpreter import Interpreter
from anka.runtime.interpreter import RuntimeError as AnkaRuntimeError


@pytest.fixture
def parser() -> Parser:
    """Create a parser instance."""
    return Parser()


@pytest.fixture
def interpreter() -> Interpreter:
    """Create an interpreter instance."""
    return Interpreter()


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


class TestReadOperation:
    """Tests for the READ operation."""

    def test_read_json(
        self, parser: Parser, interpreter: Interpreter, fixtures_dir: Path
    ) -> None:
        """Test reading a JSON file."""
        json_path = fixtures_dir / "sample.json"
        source = f'''
        PIPELINE read_test:
            INPUT dummy: TABLE[x: INT]

            STEP load:
                READ "{json_path}"
                FORMAT JSON
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
        assert result[0]["amount"] == 1500

    def test_read_csv(
        self, parser: Parser, interpreter: Interpreter, fixtures_dir: Path
    ) -> None:
        """Test reading a CSV file."""
        csv_path = fixtures_dir / "sample.csv"
        source = f'''
        PIPELINE read_csv_test:
            INPUT dummy: TABLE[x: INT]

            STEP load:
                READ "{csv_path}"
                FORMAT CSV
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
        # CSV values should be converted to numbers
        assert result[0]["amount"] == 1500
        assert result[1]["amount"] == 800

    def test_read_file_not_found(
        self, parser: Parser, interpreter: Interpreter
    ) -> None:
        """Test error when file doesn't exist."""
        source = '''
        PIPELINE read_missing:
            INPUT dummy: TABLE[x: INT]

            STEP load:
                READ "nonexistent_file.json"
                FORMAT JSON
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        with pytest.raises(AnkaRuntimeError, match="File not found"):
            interpreter.execute(ast, {"dummy": []})

    def test_read_with_env_var(
        self, parser: Parser, interpreter: Interpreter, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test reading a file with environment variable in path."""
        monkeypatch.setenv("TEST_FIXTURES_DIR", str(fixtures_dir))

        source = '''
        PIPELINE read_env_test:
            INPUT dummy: TABLE[x: INT]

            STEP load:
                READ "${TEST_FIXTURES_DIR}/sample.json"
                FORMAT JSON
                INTO data

            OUTPUT data
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 3

    def test_read_with_filter(
        self, parser: Parser, interpreter: Interpreter, fixtures_dir: Path
    ) -> None:
        """Test reading a file and filtering the data."""
        json_path = fixtures_dir / "sample.json"
        source = f'''
        PIPELINE read_and_filter:
            INPUT dummy: TABLE[x: INT]

            STEP load:
                READ "{json_path}"
                FORMAT JSON
                INTO data

            STEP filter_high:
                FILTER data
                WHERE amount > 1000
                INTO high_value

            OUTPUT high_value
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        assert result is not None
        assert len(result) == 2
        assert all(row["amount"] > 1000 for row in result)


class TestWriteOperation:
    """Tests for the WRITE operation."""

    def test_write_json(
        self, parser: Parser, interpreter: Interpreter, tmp_path: Path
    ) -> None:
        """Test writing data to a JSON file."""
        output_path = tmp_path / "output.json"
        source = f'''
        PIPELINE write_test:
            INPUT data: TABLE[id: INT, name: STRING]

            STEP save:
                WRITE data
                TO "{output_path}"
                FORMAT JSON

            OUTPUT data
        '''
        input_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": input_data})

        # Verify file was written
        assert output_path.exists()
        with open(output_path) as f:
            written_data = json.load(f)
        assert written_data == input_data

    def test_write_csv(
        self, parser: Parser, interpreter: Interpreter, tmp_path: Path
    ) -> None:
        """Test writing data to a CSV file."""
        output_path = tmp_path / "output.csv"
        source = f'''
        PIPELINE write_csv_test:
            INPUT data: TABLE[id: INT, name: STRING, amount: DECIMAL]

            STEP save:
                WRITE data
                TO "{output_path}"
                FORMAT CSV

            OUTPUT data
        '''
        input_data = [
            {"id": 1, "name": "Alice", "amount": 1500},
            {"id": 2, "name": "Bob", "amount": 800},
        ]
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": input_data})

        # Verify file was written
        assert output_path.exists()
        content = output_path.read_text()
        assert "id,name,amount" in content
        assert "Alice" in content
        assert "Bob" in content

    def test_write_creates_parent_dirs(
        self, parser: Parser, interpreter: Interpreter, tmp_path: Path
    ) -> None:
        """Test that WRITE creates parent directories."""
        output_path = tmp_path / "nested" / "deep" / "output.json"
        source = f'''
        PIPELINE write_nested:
            INPUT data: TABLE[x: INT]

            STEP save:
                WRITE data
                TO "{output_path}"
                FORMAT JSON

            OUTPUT data
        '''
        ast = parser.parse(source)
        interpreter.execute(ast, {"data": [{"x": 1}]})

        assert output_path.exists()

    def test_write_source_not_found(
        self, parser: Parser, interpreter: Interpreter, tmp_path: Path
    ) -> None:
        """Test error when source variable doesn't exist."""
        output_path = tmp_path / "output.json"
        source = f'''
        PIPELINE write_missing:
            INPUT data: TABLE[x: INT]

            STEP save:
                WRITE nonexistent
                TO "{output_path}"
                FORMAT JSON

            OUTPUT data
        '''
        ast = parser.parse(source)
        with pytest.raises(AnkaRuntimeError, match="not found in environment"):
            interpreter.execute(ast, {"data": []})


class TestReadWritePipeline:
    """Tests for combined read/write pipelines."""

    def test_read_transform_write(
        self, parser: Parser, interpreter: Interpreter, fixtures_dir: Path, tmp_path: Path
    ) -> None:
        """Test reading, transforming, and writing data."""
        json_path = fixtures_dir / "sample.json"
        output_path = tmp_path / "filtered.json"

        source = f'''
        PIPELINE etl:
            INPUT dummy: TABLE[x: INT]

            STEP load:
                READ "{json_path}"
                FORMAT JSON
                INTO data

            STEP filter_high:
                FILTER data
                WHERE amount > 1000
                INTO filtered

            STEP save:
                WRITE filtered
                TO "{output_path}"
                FORMAT JSON

            OUTPUT filtered
        '''
        ast = parser.parse(source)
        result = interpreter.execute(ast, {"dummy": []})

        # Check result
        assert result is not None
        assert len(result) == 2

        # Check written file
        assert output_path.exists()
        with open(output_path) as f:
            written_data = json.load(f)
        assert len(written_data) == 2
        assert all(row["amount"] > 1000 for row in written_data)
