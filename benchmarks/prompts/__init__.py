"""Prompt templates for LLM code generation."""

from pathlib import Path
from typing import Any

from benchmarks.schema import BenchmarkTask


PROMPTS_DIR = Path(__file__).parent


def format_schema(schema: dict[str, Any]) -> str:
    """Format input schema for display in prompts.

    Supports two schema formats:
    - Old format: {table: [{name: str, type: str}, ...]}
    - New format: {table: {columns: [str], types: [str]}}

    Args:
        schema: Dictionary mapping table names to column definitions.

    Returns:
        Human-readable schema description.
    """
    lines = []
    for table_name, columns in schema.items():
        if isinstance(columns, dict) and "columns" in columns:
            # New format: {columns: [...], types: [...]}
            col_strs = [
                f"{col}: {typ}"
                for col, typ in zip(columns["columns"], columns["types"])
            ]
        elif isinstance(columns, list):
            # Old format: list of {name, type} dicts
            col_strs = [f"{col['name']}: {col['type']}" for col in columns]
        else:
            # Unknown format - skip
            continue
        lines.append(f"- {table_name}: TABLE[{', '.join(col_strs)}]")
    return "\n".join(lines)


def load_prompt(language: str, task: BenchmarkTask) -> str:
    """Load and fill a prompt template for a task.

    Args:
        language: "anka" or "python".
        task: The benchmark task to generate code for.

    Returns:
        The filled prompt string.

    Raises:
        FileNotFoundError: If the prompt template doesn't exist.
        ValueError: If the language is not supported.
    """
    if language == "anka":
        template_path = PROMPTS_DIR / "anka_prompt.md"
    elif language == "python":
        template_path = PROMPTS_DIR / "python_prompt.md"
    else:
        raise ValueError(f"Unsupported language: {language}")

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    template = template_path.read_text()

    # Format the schema
    schema_str = format_schema(task.input_schema)

    # Use prompt field if available, otherwise fall back to description
    task_prompt = task.prompt if task.prompt else task.description

    # Use simple string replacement instead of .format() to avoid
    # issues with curly braces in the template content
    result = template.replace("{description}", task_prompt)
    result = result.replace("{input_schema}", schema_str)
    return result
