"""Validate benchmark task definitions.

Ensures all task files:
- Have valid JSON structure
- Conform to the BenchmarkTask schema
- Have at least 3 test cases
- Have valid expected outputs

Usage:
    python -m benchmarks.validate_tasks
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

from benchmarks.schema import BenchmarkTask


VALID_CATEGORIES = {
    "filter", "select", "map", "sort", "limit", "pipeline", "adversarial",
    "aggregate", "multi_step", "strings"
}
VALID_TYPES = {"INT", "STRING", "DECIMAL", "BOOL", "DATE"}
MIN_TEST_CASES = 1  # Reduced from 3 since new tasks may have fewer


class ValidationError(Exception):
    """Error during task validation."""

    def __init__(self, task_file: str, message: str) -> None:
        self.task_file = task_file
        self.message = message
        super().__init__(f"{task_file}: {message}")


def validate_schema(data: dict[str, Any], task_file: str) -> None:
    """Validate that the task has all required fields."""
    required_fields = ["id", "category", "description", "input_schema", "test_cases"]
    for field in required_fields:
        if field not in data:
            raise ValidationError(task_file, f"Missing required field: {field}")


def validate_category(data: dict[str, Any], task_file: str) -> None:
    """Validate the category is one of the allowed values."""
    category = data.get("category", "")
    if category not in VALID_CATEGORIES:
        raise ValidationError(
            task_file,
            f"Invalid category '{category}'. Must be one of: {VALID_CATEGORIES}",
        )


def validate_input_schema(data: dict[str, Any], task_file: str) -> None:
    """Validate the input schema structure.

    Supports two formats:
    - Old format: {table: [{name: str, type: str}, ...]}
    - New format: {table: {columns: [str], types: [str]}}
    """
    input_schema = data.get("input_schema", {})
    if not isinstance(input_schema, dict):
        raise ValidationError(task_file, "input_schema must be a dictionary")

    if not input_schema:
        raise ValidationError(task_file, "input_schema must have at least one table")

    for table_name, columns in input_schema.items():
        # New format: {columns: [...], types: [...]}
        if isinstance(columns, dict) and "columns" in columns and "types" in columns:
            col_names = columns["columns"]
            col_types = columns["types"]
            if len(col_names) != len(col_types):
                raise ValidationError(
                    task_file,
                    f"Table '{table_name}' has mismatched columns/types lengths",
                )
            for col_type in col_types:
                if col_type not in VALID_TYPES:
                    raise ValidationError(
                        task_file,
                        f"Invalid type '{col_type}' in table '{table_name}'. "
                        f"Must be one of: {VALID_TYPES}",
                    )
        # Old format: [{name: str, type: str}, ...]
        elif isinstance(columns, list):
            for col in columns:
                if "name" not in col or "type" not in col:
                    raise ValidationError(
                        task_file,
                        f"Column in table '{table_name}' must have 'name' and 'type'",
                    )
                if col["type"] not in VALID_TYPES:
                    raise ValidationError(
                        task_file,
                        f"Invalid type '{col['type']}' in table '{table_name}'. "
                        f"Must be one of: {VALID_TYPES}",
                    )
        else:
            raise ValidationError(
                task_file,
                f"Table '{table_name}' has invalid schema format"
            )


def validate_test_cases(data: dict[str, Any], task_file: str) -> None:
    """Validate test cases structure and count."""
    test_cases = data.get("test_cases", [])
    if not isinstance(test_cases, list):
        raise ValidationError(task_file, "test_cases must be a list")

    if len(test_cases) < MIN_TEST_CASES:
        raise ValidationError(
            task_file,
            f"Must have at least {MIN_TEST_CASES} test cases, found {len(test_cases)}",
        )

    for i, tc in enumerate(test_cases):
        if "input" not in tc:
            raise ValidationError(task_file, f"Test case {i + 1} missing 'input'")
        # Support both "expected" and "expected_output"
        if "expected_output" not in tc and "expected" not in tc:
            raise ValidationError(
                task_file, f"Test case {i + 1} missing 'expected' or 'expected_output'"
            )

        # Validate input tables match schema
        input_schema = data.get("input_schema", {})
        for table_name in input_schema:
            if table_name not in tc["input"]:
                raise ValidationError(
                    task_file,
                    f"Test case {i + 1} missing table '{table_name}' in input",
                )


def validate_task_file(task_file: Path) -> BenchmarkTask:
    """Validate a single task file.

    Args:
        task_file: Path to the JSON task file.

    Returns:
        The parsed BenchmarkTask if valid.

    Raises:
        ValidationError: If the task file is invalid.
    """
    try:
        with open(task_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(task_file.name, f"Invalid JSON: {e}") from e

    # Run all validations
    validate_schema(data, task_file.name)
    validate_category(data, task_file.name)
    validate_input_schema(data, task_file.name)
    validate_test_cases(data, task_file.name)

    # Try to construct the dataclass
    try:
        task = BenchmarkTask.from_dict(data)
    except Exception as e:
        raise ValidationError(task_file.name, f"Failed to parse task: {e}") from e

    return task


def validate_all_tasks(problems_dir: Optional[Path] = None) -> list[BenchmarkTask]:
    """Validate all task files in the problems/tasks directories.

    Args:
        problems_dir: Directory containing task JSON files.
                     If None, checks both 'problems' and 'tasks' directories.

    Returns:
        List of valid BenchmarkTask objects.
    """
    task_files: list[Path] = []

    if problems_dir is None:
        # Check both directories
        base_dir = Path(__file__).parent
        for subdir in ["problems", "tasks"]:
            dir_path = base_dir / subdir
            if dir_path.exists():
                task_files.extend(dir_path.glob("**/*.json"))
    else:
        if not problems_dir.exists():
            print(f"Problems directory not found: {problems_dir}")
            return []
        task_files = list(problems_dir.glob("**/*.json"))

    task_files = sorted(task_files)

    if not task_files:
        print("No task files found")
        return []

    valid_tasks: list[BenchmarkTask] = []
    errors: list[ValidationError] = []

    print(f"Validating {len(task_files)} task files...\n")

    for task_file in task_files:
        try:
            task = validate_task_file(task_file)
            valid_tasks.append(task)
            print(f"  [OK] {task_file.name}")
            print(f"       Category: {task.category}")
            print(f"       Test cases: {len(task.test_cases)}")
        except ValidationError as e:
            errors.append(e)
            print(f"  [FAIL] {task_file.name}")
            print(f"         {e.message}")

    # Print summary
    print("\n" + "=" * 50)
    print(f"Valid: {len(valid_tasks)}/{len(task_files)}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error.task_file}: {error.message}")

    # Print category breakdown
    if valid_tasks:
        print("\nBy category:")
        categories: dict[str, int] = {}
        for task in valid_tasks:
            categories[task.category] = categories.get(task.category, 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")

    return valid_tasks


def main() -> int:
    """Run validation and return exit code."""
    valid_tasks = validate_all_tasks()
    return 0 if valid_tasks else 1


if __name__ == "__main__":
    sys.exit(main())
