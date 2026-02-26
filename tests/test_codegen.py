"""Tests for Python code generation."""

from anka.codegen.python_emitter import PythonEmitter
from anka.grammar.parser import Parser


class TestPythonEmitter:
    """Tests for the Python code emitter."""

    def test_emitter_initializes(self) -> None:
        """Emitter should initialize without error."""
        emitter = PythonEmitter()
        assert emitter is not None

    def test_emit_produces_python(self) -> None:
        """Emit should produce Python code string."""
        parser = Parser()
        source = """
        PIPELINE test:
            INPUT data: TABLE[x: INT]
            OUTPUT data
        """
        ast = parser.parse(source)

        emitter = PythonEmitter()
        code = emitter.emit(ast)

        assert isinstance(code, str)
        assert "import pandas" in code
        assert "def test" in code

    def test_emit_uses_pipeline_name(self) -> None:
        """Generated function should use pipeline name."""
        parser = Parser()
        source = """
        PIPELINE my_custom_pipeline:
            INPUT data: TABLE[x: INT]
            OUTPUT data
        """
        ast = parser.parse(source)

        emitter = PythonEmitter()
        code = emitter.emit(ast)

        assert "def my_custom_pipeline" in code
