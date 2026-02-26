"""Command-line interface for Anka."""

import json
import sys
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from anka import __version__
from anka.ast.visitors import ASTPrinter
from anka.grammar.parser import Parser
from anka.runtime.interpreter import Interpreter
from anka.runtime.interpreter import RuntimeError as AnkaRuntimeError

console = Console()
error_console = Console(stderr=True)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="anka")
@click.option("--repl", is_flag=True, help="Start interactive REPL")
@click.pass_context
def main(ctx: click.Context, repl: bool) -> None:
    """Anka: LLM-optimized DSL for data transformations.

    Run an Anka file or start the interactive REPL.

    Examples:
        anka run program.anka data.json    # Execute with input data
        anka parse program.anka            # Parse and show AST
        anka check program.anka            # Check for errors
        anka --repl                        # Start interactive REPL
    """
    if repl:
        run_repl()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def run_file(path: str, input_file: Optional[str] = None) -> None:
    """Parse and optionally execute an Anka file.

    Args:
        path: Path to the .anka file.
        input_file: Optional path to JSON file with input data.
    """
    try:
        parser = Parser()
        ast = parser.parse_file(path)

        if input_file:
            # Execute the pipeline with input data
            inputs = load_input_data(input_file)
            interpreter = Interpreter()
            result = interpreter.execute(ast, inputs)

            # Print the result as JSON
            console.print(Panel(
                f"[bold]Pipeline:[/bold] {ast.name.name}",
                title="[bold blue]Execution Result[/bold blue]",
                border_style="blue",
            ))
            console.print_json(data=result)
        else:
            # Just print the AST
            printer = ASTPrinter()
            printer.visit(ast)

            console.print(Panel(
                printer.get_output(),
                title=f"[bold green]AST for {Path(path).name}[/bold green]",
                border_style="green",
            ))

    except FileNotFoundError:
        error_console.print(f"[red]Error:[/red] File not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        error_console.print(f"[red]JSON Error:[/red] {e}")
        sys.exit(1)
    except AnkaRuntimeError as e:
        error_console.print(f"[red]Runtime Error:[/red] {e.message}")
        sys.exit(1)
    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def load_input_data(input_file: str) -> dict[str, list[dict[str, Any]]]:
    """Load input data from a JSON file.

    Args:
        input_file: Path to JSON file.

    Returns:
        Dictionary mapping input names to table data.

    Raises:
        json.JSONDecodeError: If JSON is invalid.
        FileNotFoundError: If file doesn't exist.
    """
    with open(input_file, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def run_repl() -> None:
    """Start the interactive REPL."""
    console.print(Panel(
        f"Anka REPL v{__version__}\n"
        "Type 'exit' or 'quit' to exit, 'help' for help.",
        title="[bold blue]Welcome to Anka[/bold blue]",
        border_style="blue",
    ))

    parser = Parser()
    buffer: list[str] = []

    while True:
        try:
            prompt = "... " if buffer else ">>> "
            line = console.input(f"[bold cyan]{prompt}[/bold cyan]")

            # Handle commands
            if not buffer:
                if line.lower() in ("exit", "quit"):
                    console.print("[dim]Goodbye![/dim]")
                    break
                if line.lower() == "help":
                    print_help()
                    continue
                if line.lower() == "clear":
                    console.clear()
                    continue
                if not line.strip():
                    continue

            buffer.append(line)

            # Try to parse if we have a complete pipeline
            source = "\n".join(buffer)
            if "OUTPUT" in source:
                try:
                    ast = parser.parse(source)
                    printer = ASTPrinter()
                    printer.visit(ast)
                    console.print()
                    console.print(Syntax(printer.get_output(), "yaml", theme="monokai"))
                    console.print()
                    buffer = []
                except Exception:
                    # Not complete yet, keep buffering
                    pass

        except KeyboardInterrupt:
            console.print("\n[dim]Use 'exit' to quit[/dim]")
            buffer = []
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break


def print_help() -> None:
    """Print REPL help message."""
    help_text = """
[bold]Commands:[/bold]
  exit, quit  Exit the REPL
  help        Show this help message
  clear       Clear the screen

[bold]Example:[/bold]
  >>> PIPELINE hello:
  ...   INPUT data: TABLE[x: INT]
  ...   OUTPUT data

[bold]The AST will be printed when a complete pipeline is entered.[/bold]
"""
    console.print(Panel(help_text, title="[bold]Help[/bold]", border_style="yellow"))


@main.command()
@click.argument("file", type=click.Path(exists=True))
def parse(file: str) -> None:
    """Parse an Anka file and print the AST."""
    run_file(file)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output errors as JSON")
def check(file: str, json_output: bool) -> None:
    """Check an Anka file for errors (parsing only for now)."""
    try:
        parser = Parser()
        parser.parse_file(file)
        if json_output:
            print(json.dumps({"status": "ok", "errors": []}))
        else:
            console.print(f"[green]OK:[/green] {file}")
    except Exception as e:
        if json_output:
            # Try to extract line/column from Lark errors
            error_info = {"message": str(e), "line": 1, "column": 1}
            error_str = str(e)
            # Lark errors often contain "at line X, column Y"
            import re
            line_match = re.search(r"line (\d+)", error_str)
            col_match = re.search(r"column (\d+)", error_str)
            if line_match:
                error_info["line"] = int(line_match.group(1))
            if col_match:
                error_info["column"] = int(col_match.group(1))
            print(json.dumps({"status": "error", "errors": [error_info]}))
        else:
            error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON only")
def run(file: str, input_file: str, json_output: bool) -> None:
    """Execute an Anka file with input data.

    FILE is the .anka program to execute.
    INPUT_FILE is a JSON file containing input data.
    """
    if json_output:
        run_file_json(file, input_file)
    else:
        run_file(file, input_file)


def run_file_json(path: str, input_file: str) -> None:
    """Execute an Anka file and output raw JSON.

    Args:
        path: Path to the .anka file.
        input_file: Path to JSON file with input data.
    """
    try:
        parser = Parser()
        ast = parser.parse_file(path)
        inputs = load_input_data(input_file)
        interpreter = Interpreter()
        result = interpreter.execute(ast, inputs)
        print(json.dumps(result))
    except FileNotFoundError:
        error_console.print(f"Error: File not found: {path}", style=None)
        sys.exit(1)
    except json.JSONDecodeError as e:
        error_console.print(f"JSON Error: {e}", style=None)
        sys.exit(1)
    except AnkaRuntimeError as e:
        error_console.print(f"Runtime Error: {e.message}", style=None)
        sys.exit(1)
    except Exception as e:
        error_console.print(f"Error: {e}", style=None)
        sys.exit(1)


if __name__ == "__main__":
    main()
