"""Task and result schema for LLM benchmarks.

Defines the data structures for benchmark problems, test cases,
and execution results.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union


@dataclass(frozen=True)
class TestCase:
    """A single test case for a benchmark task.

    Attributes:
        input: Dictionary mapping table names to lists of row dicts.
        expected_output: The expected output rows after transformation.
    """

    input: dict[str, list[dict[str, Any]]]
    expected_output: list[dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCase":
        """Create a TestCase from a dictionary."""
        # Support both "expected" and "expected_output" field names
        expected = data.get("expected_output") or data.get("expected")
        return cls(
            input=data["input"],
            expected_output=expected,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "input": self.input,
            "expected_output": self.expected_output,
        }


@dataclass(frozen=True)
class BenchmarkTask:
    """A benchmark task definition.

    Attributes:
        id: Unique task identifier (e.g., "filter_001").
        category: Task category (filter, select, map, sort, limit, pipeline).
        description: Natural language description of what to do.
        input_schema: Schema definition for input tables.
        test_cases: List of input/expected_output pairs for validation.
        prompt: Optional detailed prompt for the LLM (if different from description).
    """

    id: str
    category: str
    description: str
    input_schema: dict[str, list[dict[str, str]]]
    test_cases: tuple[TestCase, ...]
    prompt: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkTask":
        """Create a BenchmarkTask from a dictionary."""
        test_cases = tuple(
            TestCase.from_dict(tc) for tc in data["test_cases"]
        )
        return cls(
            id=data["id"],
            category=data["category"],
            description=data["description"],
            input_schema=data["input_schema"],
            test_cases=test_cases,
            prompt=data.get("prompt"),
        )

    @classmethod
    def from_json_file(cls, path: Union[str, Path]) -> "BenchmarkTask":
        """Load a BenchmarkTask from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "category": self.category,
            "description": self.description,
            "input_schema": self.input_schema,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ExecutionResult:
    """Result of executing generated code.

    Attributes:
        success: Whether execution completed without errors.
        output: The output data if successful.
        error: Error message if execution failed.
        execution_time_ms: How long execution took.
    """

    success: bool
    output: Optional[list[dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class GenerationResult:
    """Result of LLM code generation.

    Attributes:
        code: The generated code.
        model: Which model generated it.
        tokens_used: Total tokens consumed.
        latency_ms: API call latency.
    """

    code: str
    model: str
    tokens_used: int
    latency_ms: float


@dataclass
class TaskResult:
    """Result of running a single task.

    Attributes:
        task_id: Which task was run.
        category: Task category.
        language: "anka" or "python".
        model: Which LLM model was used.
        generated_code: The code that was generated.
        test_results: Pass/fail for each test case.
        pass_all: Whether all test cases passed.
        error: Error message if any.
        latency_ms: Total time for generation + execution.
    """

    task_id: str
    category: str
    language: str
    model: str
    generated_code: str
    test_results: list[bool] = field(default_factory=list)
    pass_all: bool = False
    error: Optional[str] = None
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "category": self.category,
            "language": self.language,
            "model": self.model,
            "generated_code": self.generated_code,
            "test_results": self.test_results,
            "pass_all": self.pass_all,
            "error": self.error,
            "latency_ms": self.latency_ms,
        }


@dataclass
class BenchmarkRun:
    """A complete benchmark run.

    Attributes:
        run_id: Unique identifier for this run.
        timestamp: When the run started.
        model: LLM model used.
        temperature: Sampling temperature.
        results: List of task results.
    """

    run_id: str
    timestamp: str
    model: str
    temperature: float
    results: list[TaskResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "model": self.model,
            "temperature": self.temperature,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: Union[str, Path]) -> None:
        """Save the benchmark run to a JSON file."""
        with open(path, "w") as f:
            f.write(self.to_json())
