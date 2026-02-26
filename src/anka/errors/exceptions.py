"""Structured error types for the Anka compiler."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Error severity levels."""

    ERROR = "error"
    WARNING = "warning"
    HINT = "hint"


@dataclass(frozen=True)
class CompilerError(Exception):
    """A structured compiler error with source location and helpful messages.

    Formats errors in Rust-style with line numbers, source context, and suggestions.

    Attributes:
        line: 1-indexed line number where the error occurred.
        column: 1-indexed column number where the error occurred.
        message: Human-readable error description.
        severity: Error severity level (error, warning, hint).
        suggestion: Optional help text for fixing the error.
        source_line: Optional source code line for context.
        file_path: Optional path to the source file.
        error_code: Optional error code (e.g., E001).
    """

    line: int
    column: int
    message: str
    severity: Severity = Severity.ERROR
    suggestion: Optional[str] = None
    source_line: Optional[str] = None
    file_path: Optional[str] = None
    error_code: Optional[str] = None

    def __str__(self) -> str:
        """Format the error in Rust-style output."""
        lines = []

        # Header line: Error[E001]: message
        severity_str = self.severity.value.capitalize()
        if self.error_code:
            lines.append(f"{severity_str}[{self.error_code}]: {self.message}")
        else:
            lines.append(f"{severity_str}: {self.message}")

        # Location line: --> file:line:column
        file_display = self.file_path or "<input>"
        lines.append(f"  --> {file_display}:{self.line}:{self.column}")

        # Source context
        if self.source_line is not None:
            line_num_width = len(str(self.line))
            padding = " " * line_num_width

            lines.append(f"   {padding}|")
            lines.append(f"   {self.line} | {self.source_line}")

            # Underline pointing to the error location
            pointer_padding = " " * (self.column - 1)
            lines.append(f"   {padding}| {pointer_padding}^")

        # Help suggestion
        if self.suggestion:
            lines.append("   |")
            lines.append(f"Help: {self.suggestion}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"CompilerError(line={self.line}, column={self.column}, "
            f"message={self.message!r}, severity={self.severity})"
        )
