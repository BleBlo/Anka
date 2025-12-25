"""Sandbox execution for generated code.

Provides isolated execution environments for Anka and Python code,
with timeouts and output capture.
"""

import json
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from benchmarks.schema import ExecutionResult


DEFAULT_TIMEOUT_SECONDS = 5


class Executor(ABC):
    """Abstract base class for code executors."""

    @abstractmethod
    def execute(
        self,
        code: str,
        inputs: dict[str, list[dict[str, Any]]],
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        """Execute code with given inputs.

        Args:
            code: The code to execute.
            inputs: Dictionary mapping table names to row data.
            timeout: Maximum execution time in seconds.

        Returns:
            ExecutionResult with success status and output or error.
        """
        pass


class AnkaExecutor(Executor):
    """Executes Anka code by running it through the Anka interpreter.

    Uses subprocess for isolation and timeout control.
    """

    def execute(
        self,
        code: str,
        inputs: dict[str, list[dict[str, Any]]],
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        """Execute Anka code.

        Args:
            code: Anka pipeline code.
            inputs: Input data for the pipeline.
            timeout: Maximum execution time in seconds.

        Returns:
            ExecutionResult with the pipeline output.
        """
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write the Anka code
            anka_file = tmppath / "program.anka"
            anka_file.write_text(code)

            # Write the input data
            input_file = tmppath / "input.json"
            input_file.write_text(json.dumps(inputs, indent=2))

            try:
                # Run Anka interpreter with --json for raw output
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "anka",
                        "run",
                        str(anka_file),
                        str(input_file),
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=Path(__file__).parent.parent,  # Project root
                )

                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if result.returncode != 0:
                    return ExecutionResult(
                        success=False,
                        error=result.stderr.strip() or result.stdout.strip(),
                        execution_time_ms=elapsed_ms,
                    )

                # Parse the JSON output
                try:
                    output = json.loads(result.stdout)
                    return ExecutionResult(
                        success=True,
                        output=output,
                        execution_time_ms=elapsed_ms,
                    )
                except json.JSONDecodeError as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Failed to parse output: {e}\nOutput: {result.stdout}",
                        execution_time_ms=elapsed_ms,
                    )

            except subprocess.TimeoutExpired:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {timeout} seconds",
                    execution_time_ms=elapsed_ms,
                )
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    error=f"Execution error: {e}",
                    execution_time_ms=elapsed_ms,
                )


class PythonExecutor(Executor):
    """Executes Python transformation code in a subprocess.

    The generated Python code is expected to define a function:
        def transform(data: dict) -> list[dict]

    where 'data' is a dict mapping table names to lists of row dicts.
    """

    WRAPPER_TEMPLATE = '''
import json
import sys

{code}

# Read input
with open(sys.argv[1]) as f:
    data = json.load(f)

# Execute transform
result = transform(data)

# Output result
print(json.dumps(result))
'''

    def execute(
        self,
        code: str,
        inputs: dict[str, list[dict[str, Any]]],
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> ExecutionResult:
        """Execute Python transformation code.

        Args:
            code: Python code containing a `transform(data)` function.
            inputs: Input data for the transformation.
            timeout: Maximum execution time in seconds.

        Returns:
            ExecutionResult with the transformation output.
        """
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write the wrapper script
            wrapped_code = self.WRAPPER_TEMPLATE.format(code=code)
            python_file = tmppath / "transform.py"
            python_file.write_text(wrapped_code)

            # Write the input data
            input_file = tmppath / "input.json"
            input_file.write_text(json.dumps(inputs, indent=2))

            try:
                # Run Python code
                result = subprocess.run(
                    [sys.executable, str(python_file), str(input_file)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )

                elapsed_ms = (time.perf_counter() - start_time) * 1000

                if result.returncode != 0:
                    return ExecutionResult(
                        success=False,
                        error=result.stderr.strip() or result.stdout.strip(),
                        execution_time_ms=elapsed_ms,
                    )

                # Parse the JSON output
                try:
                    output = json.loads(result.stdout)
                    return ExecutionResult(
                        success=True,
                        output=output,
                        execution_time_ms=elapsed_ms,
                    )
                except json.JSONDecodeError as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Failed to parse output: {e}\nOutput: {result.stdout}",
                        execution_time_ms=elapsed_ms,
                    )

            except subprocess.TimeoutExpired:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {timeout} seconds",
                    execution_time_ms=elapsed_ms,
                )
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    error=f"Execution error: {e}",
                    execution_time_ms=elapsed_ms,
                )


def compare_outputs(
    actual: Any,
    expected: Any,
) -> bool:
    """Compare actual output to expected output.

    Args:
        actual: The actual output from execution.
        expected: The expected output.

    Returns:
        True if outputs match, False otherwise.
    """
    # Handle None
    if actual is None:
        return expected is None or expected == []

    # Handle scalar values (int, float, str, bool)
    if isinstance(expected, (int, float)):
        if isinstance(actual, (int, float)):
            return abs(actual - expected) < 1e-9
        return False
    if isinstance(expected, str):
        return actual == expected
    if isinstance(expected, bool):
        return actual == expected

    # Handle dict (single record output)
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return _compare_dicts(actual, expected)

    # Handle list (table output)
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        if len(actual) != len(expected):
            return False
        for act_row, exp_row in zip(actual, expected):
            if isinstance(exp_row, dict):
                if not isinstance(act_row, dict):
                    return False
                if not _compare_dicts(act_row, exp_row):
                    return False
            else:
                if act_row != exp_row:
                    return False
        return True

    # Fallback: direct comparison
    return actual == expected


def _compare_dicts(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Compare two dictionaries, handling floating point values."""
    if set(actual.keys()) != set(expected.keys()):
        return False
    for key in expected:
        act_val = actual.get(key)
        exp_val = expected[key]
        if act_val != exp_val:
            # Handle floating point comparison
            if isinstance(act_val, (int, float)) and isinstance(exp_val, (int, float)):
                if abs(act_val - exp_val) > 1e-9:
                    return False
            else:
                return False
    return True


def get_executor(language: str) -> Executor:
    """Get the appropriate executor for a language.

    Args:
        language: "anka" or "python".

    Returns:
        The corresponding Executor instance.

    Raises:
        ValueError: If the language is not supported.
    """
    if language == "anka":
        return AnkaExecutor()
    elif language == "python":
        return PythonExecutor()
    else:
        raise ValueError(f"Unsupported language: {language}")
