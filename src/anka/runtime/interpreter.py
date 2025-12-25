"""Tree-walking interpreter for Anka."""

import csv
import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

import requests
from dateutil.relativedelta import relativedelta

from anka.ast.nodes import (
    AddColumn,
    Aggregate,
    AndExpr,
    AppendStatement,
    ArithmeticOp,
    AssertStatement,
    BetweenCheck,
    BinaryOp,
    BreakStatement,
    Coalesce,
    Condition,
    ContinueStatement,
    DateCheck,
    DateFunc,
    Distinct,
    Drop,
    Fetch,
    Filter,
    ForEachStatement,
    Identifier,
    IfExpr,
    IfStatement,
    InCheck,
    IsNullCheck,
    Join,
    LeftJoin,
    Limit,
    ListFunc,
    Literal,
    LogStatement,
    Map,
    MatchStatement,
    MathFunc,
    NotExpr,
    NullIf,
    ObjectLiteral,
    OrExpr,
    Pipeline,
    Post,
    PrintStatement,
    Read,
    Rename,
    ReturnStatement,
    Select,
    SetStatement,
    Skip,
    Slice,
    Sort,
    Step,
    StringCheck,
    StringFunc,
    TryStatement,
    TypeCheck,
    TypeFunc,
    UnionOp,
    WhileStatement,
    Write,
)


class RuntimeError(Exception):
    """Runtime error during pipeline execution."""

    def __init__(self, message: str) -> None:
        """Initialize with error message."""
        self.message = message
        super().__init__(message)


class AssertionError(Exception):
    """Raised when an ASSERT statement fails."""

    def __init__(self, message: str) -> None:
        """Initialize with error message."""
        self.message = message
        super().__init__(message)


class ReturnSignal(Exception):
    """Signal for early return from pipeline."""

    def __init__(self, value: Optional[Any] = None) -> None:
        """Initialize with return value."""
        self.value = value
        super().__init__()


class BreakSignal(Exception):
    """Signal for breaking out of a loop."""

    pass


class ContinueSignal(Exception):
    """Signal for continuing to next loop iteration."""

    pass


class Interpreter:
    """Executes Anka programs by walking the AST.

    The interpreter maintains an environment mapping variable names
    to data (lists of dictionaries representing tables).
    """

    def __init__(self) -> None:
        """Initialize the interpreter with an empty environment."""
        self._environment: dict[str, list[dict[str, Any]]] = {}
        self._scalars: dict[str, Any] = {}

    def get_scalar(self, name: str) -> Any:
        """Get the value of a scalar variable.

        Args:
            name: The variable name.

        Returns:
            The variable value.

        Raises:
            KeyError: If variable not found.
        """
        return self._scalars[name]

    def get_scalars(self) -> dict[str, Any]:
        """Get all scalar variables.

        Returns:
            Dictionary of scalar variable names to values.
        """
        return dict(self._scalars)

    def execute(
        self, ast: Pipeline, inputs: Optional[dict[str, list[dict[str, Any]]]] = None
    ) -> Optional[list[dict[str, Any]]]:
        """Execute an Anka pipeline.

        Args:
            ast: The Pipeline AST to execute.
            inputs: Dictionary mapping input names to table data.
                    Each table is a list of dicts (rows).

        Returns:
            The pipeline output (list of dicts) or None.

        Raises:
            RuntimeError: If execution fails (missing data, invalid field, etc.)
            AssertionError: If an ASSERT statement fails.
        """
        # Reset environment for fresh execution
        self._environment = {}
        # Reset scalar variables
        self._scalars = {}

        # Load inputs into environment
        if inputs:
            self._environment.update(inputs)

        # Execute body items (steps and statements) in order
        # Use body if available, otherwise fall back to steps for backward compatibility
        body_items = ast.body if ast.body else ast.steps
        try:
            self._execute_body(body_items)
        except ReturnSignal as ret:
            # Early return - use the returned value if provided
            if ret.value is not None:
                if isinstance(ret.value, list):
                    return ret.value
                return [ret.value] if isinstance(ret.value, dict) else None
            return None

        # Return output
        if ast.outputs:
            output_name = ast.outputs.name.name
            if output_name in self._environment:
                return self._environment[output_name]
            raise RuntimeError(f"Output '{output_name}' not found in environment")

        return None

    def _execute_step(self, step: Step) -> None:
        """Execute a single step.

        Args:
            step: The Step AST node to execute.
        """
        operation = step.operation
        if isinstance(operation, Filter):
            self._execute_filter(operation)
        elif isinstance(operation, Select):
            self._execute_select(operation)
        elif isinstance(operation, Map):
            self._execute_map(operation)
        elif isinstance(operation, Sort):
            self._execute_sort(operation)
        elif isinstance(operation, Limit):
            self._execute_limit(operation)
        elif isinstance(operation, Skip):
            self._execute_skip(operation)
        elif isinstance(operation, Distinct):
            self._execute_distinct(operation)
        elif isinstance(operation, Aggregate):
            self._execute_aggregate(operation)
        elif isinstance(operation, Read):
            self._execute_read(operation)
        elif isinstance(operation, Write):
            self._execute_write(operation)
        elif isinstance(operation, Fetch):
            self._execute_fetch(operation)
        elif isinstance(operation, Post):
            self._execute_post(operation)
        elif isinstance(operation, Join):
            self._execute_join(operation)
        elif isinstance(operation, LeftJoin):
            self._execute_left_join(operation)
        elif isinstance(operation, Rename):
            self._execute_rename(operation)
        elif isinstance(operation, Drop):
            self._execute_drop(operation)
        elif isinstance(operation, UnionOp):
            self._execute_union(operation)
        elif isinstance(operation, Slice):
            self._execute_slice(operation)
        elif isinstance(operation, AddColumn):
            self._execute_add_column(operation)

    def _execute_set(self, set_stmt: SetStatement) -> None:
        """Execute a SET statement.

        Assigns a value to a scalar variable.

        Args:
            set_stmt: The SetStatement AST node to execute.
        """
        var_name = set_stmt.variable.name
        value = set_stmt.value

        # Evaluate the value
        if isinstance(value, bool):
            # Boolean literal
            self._scalars[var_name] = value
        elif isinstance(value, Literal):
            self._scalars[var_name] = value.value
        elif isinstance(value, Identifier):
            # Variable reference - check scalars first, then environment
            ref_name = value.name
            if ref_name in self._scalars:
                self._scalars[var_name] = self._scalars[ref_name]
            elif ref_name in self._environment:
                self._scalars[var_name] = self._environment[ref_name]
            else:
                raise RuntimeError(f"Variable '{ref_name}' not found")
        else:
            # Arithmetic expression - evaluate with empty row context
            self._scalars[var_name] = self._evaluate_arith({}, value)

    def _execute_body(self, body_items: Any) -> None:
        """Execute a sequence of body items.

        Args:
            body_items: Sequence of steps, statements, etc.

        Raises:
            ReturnSignal: If RETURN statement executed.
            BreakSignal: If BREAK statement executed.
            ContinueSignal: If CONTINUE statement executed.
            AssertionError: If ASSERT fails.
        """
        for item in body_items:
            if isinstance(item, Step):
                self._execute_step(item)
            elif isinstance(item, SetStatement):
                self._execute_set(item)
            elif isinstance(item, IfStatement):
                self._execute_if(item)
            elif isinstance(item, ForEachStatement):
                self._execute_for_each(item)
            elif isinstance(item, WhileStatement):
                self._execute_while(item)
            elif isinstance(item, TryStatement):
                self._execute_try(item)
            elif isinstance(item, MatchStatement):
                self._execute_match(item)
            elif isinstance(item, AssertStatement):
                self._execute_assert(item)
            elif isinstance(item, ReturnStatement):
                self._execute_return(item)
            elif isinstance(item, BreakStatement):
                raise BreakSignal()
            elif isinstance(item, ContinueStatement):
                raise ContinueSignal()
            elif isinstance(item, AppendStatement):
                self._execute_append(item)
            elif isinstance(item, PrintStatement):
                self._execute_print(item)
            elif isinstance(item, LogStatement):
                self._execute_log(item)

    def _execute_if(self, if_stmt: IfStatement) -> None:
        """Execute an IF statement.

        Evaluates condition and executes appropriate body.

        Args:
            if_stmt: The IfStatement AST node to execute.
        """
        # Evaluate condition using scalar context
        condition_result = self._evaluate_scalar_condition(if_stmt.condition)

        if condition_result:
            self._execute_body(if_stmt.then_body)
        elif if_stmt.else_body:
            self._execute_body(if_stmt.else_body)

    def _evaluate_scalar_condition(self, condition: Condition) -> bool:
        """Evaluate a condition in scalar context (for IF statements).

        Args:
            condition: The condition to evaluate.

        Returns:
            True if condition is satisfied, False otherwise.
        """
        # Create a pseudo-row from scalar variables for condition evaluation
        row = dict(self._scalars)
        return self._evaluate_condition(row, condition)

    def _execute_for_each(self, for_stmt: ForEachStatement) -> None:
        """Execute a FOR_EACH loop.

        Iterates over a collection and executes body for each item.
        Handles BREAK and CONTINUE signals.

        Args:
            for_stmt: The ForEachStatement AST node to execute.
        """
        item_var_name = for_stmt.item_var.name
        collection_name = for_stmt.collection.name

        # Get collection from environment or scalars
        if collection_name in self._environment:
            collection = self._environment[collection_name]
        elif collection_name in self._scalars:
            collection = self._scalars[collection_name]
        else:
            raise RuntimeError(f"Collection '{collection_name}' not found")

        # Ensure collection is iterable
        if not isinstance(collection, (list, tuple)):
            raise RuntimeError(f"'{collection_name}' is not iterable")

        # Iterate and execute body
        for item in collection:
            # Set the loop variable
            self._scalars[item_var_name] = item
            try:
                self._execute_body(for_stmt.body)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _execute_while(self, while_stmt: WhileStatement) -> None:
        """Execute a WHILE loop.

        Executes body while condition is true, with max iteration limit.
        Handles BREAK and CONTINUE signals.

        Args:
            while_stmt: The WhileStatement AST node to execute.

        Raises:
            RuntimeError: If max iterations exceeded.
        """
        iterations = 0
        max_iterations = while_stmt.max_iterations

        while self._evaluate_scalar_condition(while_stmt.condition):
            try:
                self._execute_body(while_stmt.body)
            except BreakSignal:
                break
            except ContinueSignal:
                pass  # Continue to next iteration
            iterations += 1
            if iterations >= max_iterations:
                raise RuntimeError(
                    f"WHILE loop exceeded maximum iterations ({max_iterations})"
                )

    def _execute_try(self, try_stmt: TryStatement) -> None:
        """Execute a TRY/ON_ERROR statement.

        Attempts to execute try_body, and if an error occurs,
        executes error_body instead.

        Args:
            try_stmt: The TryStatement AST node to execute.
        """
        try:
            self._execute_body(try_stmt.try_body)
        except Exception:
            # On any error, execute the error handler body
            self._execute_body(try_stmt.error_body)

    def _execute_match(self, match_stmt: MatchStatement) -> None:
        """Execute a MATCH pattern matching statement.

        Matches a variable value against cases and executes the matching body.

        Args:
            match_stmt: The MatchStatement AST node to execute.
        """
        var_name = match_stmt.variable.name

        # Get the value to match
        if var_name in self._scalars:
            match_value = self._scalars[var_name]
        elif var_name in self._environment:
            match_value = self._environment[var_name]
        else:
            raise RuntimeError(f"Variable '{var_name}' not found for MATCH")

        # Try each case
        for case in match_stmt.cases:
            if match_value == case.value:
                self._execute_body(case.body)
                return

        # No case matched, execute default if present
        if match_stmt.default_body:
            self._execute_body(match_stmt.default_body)

    def _execute_assert(self, assert_stmt: AssertStatement) -> None:
        """Execute an ASSERT statement.

        Validates that condition is true, raises error if false.

        Args:
            assert_stmt: The AssertStatement AST node to execute.

        Raises:
            AssertionError: If the assertion fails.
        """
        condition_result = self._evaluate_scalar_condition(assert_stmt.condition)

        if not condition_result:
            message = assert_stmt.message or "Assertion failed"
            raise AssertionError(message)

    def _execute_return(self, return_stmt: ReturnStatement) -> None:
        """Execute a RETURN statement.

        Signals early exit from pipeline with optional value.

        Args:
            return_stmt: The ReturnStatement AST node to execute.

        Raises:
            ReturnSignal: Always raised to signal early exit.
        """
        value = None
        if return_stmt.value:
            var_name = return_stmt.value.name
            if var_name in self._environment:
                value = self._environment[var_name]
            elif var_name in self._scalars:
                value = self._scalars[var_name]
            else:
                raise RuntimeError(f"Return variable '{var_name}' not found")
        raise ReturnSignal(value)

    def _execute_append(self, append_stmt: AppendStatement) -> None:
        """Execute an APPEND statement.

        Appends source data to target collection.

        Args:
            append_stmt: The AppendStatement AST node to execute.
        """
        source_name = append_stmt.source.name
        target_name = append_stmt.target.name

        # Get source data
        if source_name in self._environment:
            source_data = self._environment[source_name]
        elif source_name in self._scalars:
            source_data = self._scalars[source_name]
        else:
            raise RuntimeError(f"Source '{source_name}' not found for APPEND")

        # Get or create target collection
        if target_name in self._environment:
            target_data = self._environment[target_name]
        else:
            # Create new empty list if target doesn't exist
            target_data = []
            self._environment[target_name] = target_data

        # Append source to target
        if isinstance(source_data, list):
            target_data.extend(source_data)
        elif isinstance(source_data, dict):
            target_data.append(source_data)
        else:
            # Scalar value - wrap in a dict or append directly
            target_data.append(source_data)

    def _execute_filter(self, filter_op: Filter) -> None:
        """Execute a FILTER operation.

        Reads data from source, filters rows by condition,
        stores result in target.

        Args:
            filter_op: The Filter AST node to execute.

        Raises:
            RuntimeError: If source data not found.
        """
        source_name = filter_op.source.name
        target_name = filter_op.target.name
        condition = filter_op.condition

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Filter rows that match the condition
        result = [row for row in source_data if self._evaluate_condition(row, condition)]

        # Store result
        self._environment[target_name] = result

    def _execute_select(self, select_op: Select) -> None:
        """Execute a SELECT operation.

        Extracts specified columns from source data,
        stores result in target.

        Args:
            select_op: The Select AST node to execute.

        Raises:
            RuntimeError: If source data not found or column doesn't exist.
        """
        source_name = select_op.source.name
        target_name = select_op.target.name
        column_names = [col.name for col in select_op.columns]

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Project columns
        result = []
        for row in source_data:
            new_row = {}
            for col_name in column_names:
                if col_name not in row:
                    raise RuntimeError(
                        f"Column '{col_name}' not found in source '{source_name}'"
                    )
                new_row[col_name] = row[col_name]
            result.append(new_row)

        # Store result
        self._environment[target_name] = result

    def _execute_map(self, map_op: Map) -> None:
        """Execute a MAP operation.

        Computes a new column for each row using the expression,
        stores result in target.

        Args:
            map_op: The Map AST node to execute.

        Raises:
            RuntimeError: If source data not found or field doesn't exist.
        """
        source_name = map_op.source.name
        target_name = map_op.target.name
        new_column_name = map_op.new_column.name
        expression = map_op.expression

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Compute new column for each row
        result = []
        for row in source_data:
            new_row = dict(row)  # Copy existing row
            new_row[new_column_name] = self._evaluate_arith(row, expression)
            result.append(new_row)

        # Store result
        self._environment[target_name] = result

    def _evaluate_arith(
        self,
        row: dict[str, Any],
        expr: Union[ArithmeticOp, Identifier, Literal, Coalesce, StringFunc, DateFunc, None],
    ) -> Any:
        """Evaluate an arithmetic expression against a row.

        Args:
            row: The row data (dict mapping field names to values).
            expr: The expression to evaluate.

        Returns:
            The computed value.

        Raises:
            RuntimeError: If a field is not found in the row.
        """
        if expr is None:
            return None

        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Identifier):
            field_name = expr.name
            # Check row first, then scalar variables
            if field_name in row:
                return row[field_name]
            if hasattr(self, '_scalars') and field_name in self._scalars:
                return self._scalars[field_name]
            raise RuntimeError(f"Field '{field_name}' not found in row or variables")

        if isinstance(expr, Coalesce):
            field_name = expr.field.name
            value = row.get(field_name)
            if value is None:
                # Default can be a Literal or an Identifier (column reference)
                if isinstance(expr.default, Identifier):
                    return row.get(expr.default.name)
                return expr.default.value
            return value

        if isinstance(expr, StringFunc):
            return self._evaluate_string_func(row, expr)

        if isinstance(expr, DateFunc):
            return self._evaluate_date_func(row, expr)

        if isinstance(expr, MathFunc):
            return self._evaluate_math_func(row, expr)

        if isinstance(expr, TypeFunc):
            return self._evaluate_type_func(row, expr)

        if isinstance(expr, ListFunc):
            return self._evaluate_list_func(row, expr)

        if isinstance(expr, IfExpr):
            return self._evaluate_if_expr(row, expr)

        if isinstance(expr, NullIf):
            return self._evaluate_nullif(row, expr)

        if isinstance(expr, ArithmeticOp):
            left = self._evaluate_arith(row, expr.left)
            right = self._evaluate_arith(row, expr.right)
            op = expr.operator

            # Handle None values in arithmetic
            if left is None or right is None:
                return None

            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise RuntimeError("Division by zero")
                return left / right

        raise RuntimeError(f"Unknown expression type: {type(expr)}")

    def _evaluate_string_func(self, row: dict[str, Any], func: StringFunc) -> Any:
        """Evaluate a string function against a row.

        Args:
            row: The row data (dict mapping field names to values).
            func: The StringFunc AST node.

        Returns:
            The computed string value.
        """
        fname = func.func_name
        args = [self._evaluate_arith(row, arg) for arg in func.args]

        if fname == "UPPER":
            return str(args[0]).upper() if args[0] is not None else ""

        if fname == "LOWER":
            return str(args[0]).lower() if args[0] is not None else ""

        if fname == "TRIM":
            return str(args[0]).strip() if args[0] is not None else ""

        if fname == "LTRIM":
            return str(args[0]).lstrip() if args[0] is not None else ""

        if fname == "RTRIM":
            return str(args[0]).rstrip() if args[0] is not None else ""

        if fname == "LENGTH":
            return len(str(args[0])) if args[0] is not None else 0

        if fname == "REVERSE":
            return str(args[0])[::-1] if args[0] is not None else ""

        if fname == "SUBSTRING":
            s, start, length = args
            if s is None:
                return ""
            return str(s)[int(start):int(start) + int(length)]

        if fname == "LEFT":
            s, count = args
            if s is None:
                return ""
            return str(s)[:int(count)]

        if fname == "RIGHT":
            s, count = args
            if s is None:
                return ""
            return str(s)[-int(count):] if int(count) > 0 else ""

        if fname == "INDEX_OF":
            s, sub = args
            if s is None:
                return -1
            return str(s).find(str(sub))

        if fname == "REPLACE":
            s, old, new = args
            if s is None:
                return ""
            return str(s).replace(str(old), str(new), 1)

        if fname == "REPLACE_ALL":
            s, old, new = args
            if s is None:
                return ""
            return str(s).replace(str(old), str(new))

        if fname == "PAD_LEFT":
            s, length, char = args
            if s is None:
                return ""
            pad_char = str(char)[0] if char else " "
            return str(s).rjust(int(length), pad_char)

        if fname == "PAD_RIGHT":
            s, length, char = args
            if s is None:
                return ""
            pad_char = str(char)[0] if char else " "
            return str(s).ljust(int(length), pad_char)

        if fname == "REPEAT":
            s, count = args
            if s is None:
                return ""
            return str(s) * int(count)

        if fname == "CONCAT":
            return "".join(str(a) if a is not None else "" for a in args)

        raise RuntimeError(f"Unknown string function: {fname}")

    def _evaluate_date_func(self, row: dict[str, Any], func: DateFunc) -> Any:
        """Evaluate a date function against a row.

        Args:
            row: The row data (dict mapping field names to values).
            func: The DateFunc AST node.

        Returns:
            The computed date/time value.
        """
        fname = func.func_name

        if fname == "NOW":
            return datetime.now()

        if fname == "TODAY":
            return date.today()

        # For functions with arguments, evaluate them
        args = [self._evaluate_arith(row, arg) for arg in func.args]

        if fname == "YEAR":
            dt = self._to_datetime(args[0])
            return dt.year if dt else None

        if fname == "MONTH":
            dt = self._to_datetime(args[0])
            return dt.month if dt else None

        if fname == "DAY":
            dt = self._to_datetime(args[0])
            return dt.day if dt else None

        if fname == "HOUR":
            dt = self._to_datetime(args[0])
            return dt.hour if dt else None

        if fname == "MINUTE":
            dt = self._to_datetime(args[0])
            return dt.minute if dt else None

        if fname == "SECOND":
            dt = self._to_datetime(args[0])
            return dt.second if dt else None

        if fname == "DAY_OF_WEEK":
            dt = self._to_datetime(args[0])
            return dt.isoweekday() if dt else None  # 1=Monday, 7=Sunday

        if fname == "WEEK_OF_YEAR":
            dt = self._to_datetime(args[0])
            return dt.isocalendar()[1] if dt else None

        if fname == "ADD_DAYS":
            dt = self._to_datetime(args[0])
            if dt is None:
                return None
            days = int(args[1])
            return dt + timedelta(days=days)

        if fname == "ADD_MONTHS":
            dt = self._to_datetime(args[0])
            if dt is None:
                return None
            months = int(args[1])
            return dt + relativedelta(months=months)

        if fname == "ADD_YEARS":
            dt = self._to_datetime(args[0])
            if dt is None:
                return None
            years = int(args[1])
            return dt + relativedelta(years=years)

        if fname == "ADD_HOURS":
            dt = self._to_datetime(args[0])
            if dt is None:
                return None
            hours = int(args[1])
            return dt + timedelta(hours=hours)

        if fname == "DIFF_DAYS":
            dt1 = self._to_datetime(args[0])
            dt2 = self._to_datetime(args[1])
            if dt1 is None or dt2 is None:
                return None
            return (dt1 - dt2).days

        if fname == "PARSE_DATE":
            s = args[0]
            if s is None:
                return None
            pattern = self._convert_date_pattern(func.format_pattern or "")
            return datetime.strptime(str(s), pattern)

        if fname == "TO_DATE":
            # Simpler date parsing - auto-detect ISO format
            s = args[0]
            if s is None:
                return None
            return self._to_datetime(s)

        if fname == "FORMAT_DATE":
            dt = self._to_datetime(args[0])
            if dt is None:
                return None
            pattern = self._convert_date_pattern(func.format_pattern or "")
            return dt.strftime(pattern)

        raise RuntimeError(f"Unknown date function: {fname}")

    def _to_datetime(self, value: Any) -> Optional[datetime]:
        """Convert value to datetime.

        Args:
            value: Value to convert.

        Returns:
            datetime object or None if conversion fails.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise RuntimeError(f"Cannot parse date: {value}")
        raise RuntimeError(f"Cannot convert to datetime: {type(value)}")

    def _convert_date_pattern(self, pattern: str) -> str:
        """Convert user-friendly pattern to strftime pattern.

        Args:
            pattern: User-friendly pattern like YYYY-MM-DD.

        Returns:
            strftime pattern like %Y-%m-%d.
        """
        return (
            pattern.replace("YYYY", "%Y")
            .replace("MM", "%m")
            .replace("DD", "%d")
            .replace("HH", "%H")
            .replace("mm", "%M")
            .replace("ss", "%S")
        )

    def _execute_sort(self, sort_op: Sort) -> None:
        """Execute a SORT operation.

        Sorts rows by a column, stores result in target.
        Handles null values according to NULLS_FIRST/NULLS_LAST.

        Args:
            sort_op: The Sort AST node to execute.

        Raises:
            RuntimeError: If source data not found or key column doesn't exist.
        """
        source_name = sort_op.source.name
        target_name = sort_op.target.name
        key_name = sort_op.key.name
        descending = sort_op.descending
        nulls_last_opt = sort_op.nulls_last

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Check that key exists in at least one row (if data not empty)
        if source_data and key_name not in source_data[0]:
            raise RuntimeError(
                f"Sort key '{key_name}' not found in source '{source_name}'"
            )

        # Determine null handling: default matches SQL behavior
        # ASC -> nulls at end, DESC -> nulls at start
        nulls_at_end = not descending if nulls_last_opt is None else nulls_last_opt

        def sort_key(row: dict[str, Any]) -> tuple[int, Any]:
            """Generate sort key that handles nulls.

            When reverse=True (DESC), Python reverses the entire tuple comparison.
            So we need to adjust the null position marker to compensate.
            """
            value = row.get(key_name)
            if value is None:
                # For nulls: we want them at position 1 (end) or 0 (start)
                # But when descending, reverse flips the comparison
                # So for DESC + NULLS_LAST: use 0 (which becomes last after reverse)
                # For DESC + NULLS_FIRST: use 1 (which becomes first after reverse)
                if descending:
                    return (0 if nulls_at_end else 1, 0)
                return (1 if nulls_at_end else 0, 0)
            # Non-nulls: position based on nulls_at_end, then actual value
            # When descending, we need to flip the null position marker
            if descending:
                return (1 if nulls_at_end else 0, value)
            return (0 if nulls_at_end else 1, value)

        # Sort the data
        result = sorted(
            source_data,
            key=sort_key,
            reverse=descending,
        )

        # Store result
        self._environment[target_name] = result

    def _execute_limit(self, limit_op: Limit) -> None:
        """Execute a LIMIT operation.

        Takes the first N rows from source, stores result in target.

        Args:
            limit_op: The Limit AST node to execute.

        Raises:
            RuntimeError: If source data not found.
        """
        source_name = limit_op.source.name
        target_name = limit_op.target.name
        count = limit_op.count

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Take the first 'count' rows
        result = source_data[:count]

        # Store result
        self._environment[target_name] = result

    def _execute_skip(self, skip_op: Skip) -> None:
        """Execute a SKIP operation.

        Skips the first N rows from source, stores result in target.

        Args:
            skip_op: The Skip AST node to execute.

        Raises:
            RuntimeError: If source data not found.
        """
        source_name = skip_op.source.name
        target_name = skip_op.target.name
        count = skip_op.count

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Skip the first 'count' rows
        result = source_data[count:]

        # Store result
        self._environment[target_name] = result

    def _execute_distinct(self, distinct_op: Distinct) -> None:
        """Execute a DISTINCT operation.

        Removes duplicate rows based on key columns, stores result in target.

        Args:
            distinct_op: The Distinct AST node to execute.

        Raises:
            RuntimeError: If source data not found.
        """
        source_name = distinct_op.source.name
        target_name = distinct_op.target.name
        key_names = [k.name for k in distinct_op.keys]

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Track seen keys and keep first occurrence
        seen: set[tuple[Any, ...]] = set()
        result = []
        for row in source_data:
            # Build key tuple from specified columns
            key = tuple(row.get(k) for k in key_names)
            if key not in seen:
                seen.add(key)
                result.append(row)

        # Store result
        self._environment[target_name] = result

    def _execute_aggregate(self, aggregate_op: Aggregate) -> None:
        """Execute an AGGREGATE operation.

        Groups rows and computes aggregate functions, stores result in target.

        Args:
            aggregate_op: The Aggregate AST node to execute.

        Raises:
            RuntimeError: If source data not found.
        """
        source_name = aggregate_op.source.name
        target_name = aggregate_op.target.name

        # Get source data
        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        source_data = self._environment[source_name]

        # Group the data
        if aggregate_op.group_by:
            group_keys = [k.name for k in aggregate_op.group_by]
            groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
            for row in source_data:
                key = tuple(row.get(k) for k in group_keys)
                groups[key].append(row)
        else:
            # No grouping - treat all data as one group
            groups = {(): source_data}

        # Compute aggregates for each group
        result = []
        for group_key, group_rows in groups.items():
            new_row: dict[str, Any] = {}

            # Add group by columns
            if aggregate_op.group_by:
                group_keys = [k.name for k in aggregate_op.group_by]
                for i, key_name in enumerate(group_keys):
                    new_row[key_name] = group_key[i]

            # Compute each aggregate
            for agg_expr in aggregate_op.computations:
                func = agg_expr.func
                alias = agg_expr.alias.name

                if func.func_name == "COUNT":
                    if func.column:
                        # COUNT(column) - count non-null values
                        col_name = func.column.name
                        count = sum(
                            1 for r in group_rows if r.get(col_name) is not None
                        )
                    else:
                        # COUNT() - count all rows
                        count = len(group_rows)
                    new_row[alias] = count

                elif func.func_name == "SUM":
                    col_name = func.column.name if func.column else ""
                    total = sum(
                        r.get(col_name, 0) or 0
                        for r in group_rows
                        if r.get(col_name) is not None
                    )
                    new_row[alias] = total

                elif func.func_name == "AVG":
                    col_name = func.column.name if func.column else ""
                    values: list[Any] = [
                        r.get(col_name)
                        for r in group_rows
                        if r.get(col_name) is not None
                    ]
                    if values:
                        new_row[alias] = sum(v for v in values) / len(values)
                    else:
                        new_row[alias] = None

                elif func.func_name == "MIN":
                    col_name = func.column.name if func.column else ""
                    min_values: list[Any] = [
                        r.get(col_name)
                        for r in group_rows
                        if r.get(col_name) is not None
                    ]
                    new_row[alias] = min(min_values) if min_values else None

                elif func.func_name == "MAX":
                    col_name = func.column.name if func.column else ""
                    max_values: list[Any] = [
                        r.get(col_name)
                        for r in group_rows
                        if r.get(col_name) is not None
                    ]
                    new_row[alias] = max(max_values) if max_values else None

            result.append(new_row)

        # Store result
        self._environment[target_name] = result

    def _evaluate_condition(self, row: dict[str, Any], condition: Condition) -> bool:
        """Evaluate a WHERE condition against a row.

        Args:
            row: The row data (dict mapping field names to values).
            condition: The condition AST node.

        Returns:
            True if the row matches the condition, False otherwise.
        """
        if isinstance(condition, BinaryOp):
            field_name = condition.left.name
            operator = condition.operator
            compare_value = condition.right.value

            # Check if field exists in row
            if field_name not in row:
                return False

            field_value = row[field_name]

            # Handle null comparisons - null doesn't match anything
            if field_value is None:
                return False

            # Perform comparison based on operator
            return self._compare(field_value, operator, compare_value)

        if isinstance(condition, IsNullCheck):
            field_name = condition.operand.name
            value = row.get(field_name)
            is_null = value is None
            return not is_null if condition.negated else is_null

        if isinstance(condition, InCheck):
            field_name = condition.operand.name
            if field_name not in row:
                return False
            field_value = row[field_name]
            if field_value is None:
                return False
            return field_value in [v.value for v in condition.values]

        if isinstance(condition, BetweenCheck):
            field_name = condition.operand.name
            if field_name not in row:
                return False
            field_value = row[field_name]
            if field_value is None:
                return False
            return bool(condition.low.value <= field_value <= condition.high.value)

        if isinstance(condition, NotExpr):
            return not self._evaluate_condition(row, condition.operand)

        if isinstance(condition, AndExpr):
            return all(
                self._evaluate_condition(row, c) for c in condition.conditions
            )

        if isinstance(condition, OrExpr):
            return any(
                self._evaluate_condition(row, c) for c in condition.conditions
            )

        if isinstance(condition, StringCheck):
            return self._evaluate_string_check(row, condition)

        if isinstance(condition, DateCheck):
            return self._evaluate_date_check(row, condition)

        if isinstance(condition, TypeCheck):
            return self._evaluate_type_check(row, condition)

        # Unknown condition type
        return False

    def _evaluate_string_check(self, row: dict[str, Any], check: StringCheck) -> bool:
        """Evaluate a string check condition against a row.

        Args:
            row: The row data (dict mapping field names to values).
            check: The StringCheck AST node.

        Returns:
            True if the check passes, False otherwise.
        """
        field_name = check.field.name
        value = row.get(field_name)
        pattern = str(check.pattern.value)

        # Null values don't match anything
        if value is None:
            return False

        value_str = str(value)

        if check.func_name == "CONTAINS":
            return pattern in value_str

        if check.func_name == "STARTS_WITH":
            return value_str.startswith(pattern)

        if check.func_name == "ENDS_WITH":
            return value_str.endswith(pattern)

        if check.func_name == "MATCHES":
            return bool(re.match(pattern, value_str))

        return False

    def _evaluate_date_check(self, row: dict[str, Any], check: DateCheck) -> bool:
        """Evaluate a date check condition against a row.

        Args:
            row: The row data (dict mapping field names to values).
            check: The DateCheck AST node.

        Returns:
            True if the check passes, False otherwise.
        """
        field_name = check.field.name
        value = row.get(field_name)

        # Null values don't match anything
        if value is None:
            return False

        dt = self._to_datetime(value)
        if dt is None:
            return False

        if check.func_name == "IS_BEFORE":
            compare_value = self._evaluate_arith(row, check.compare_value)
            compare_dt = self._to_datetime(compare_value)
            if compare_dt is None:
                return False
            return dt < compare_dt

        if check.func_name == "IS_AFTER":
            compare_value = self._evaluate_arith(row, check.compare_value)
            compare_dt = self._to_datetime(compare_value)
            if compare_dt is None:
                return False
            return dt > compare_dt

        if check.func_name == "IS_WEEKEND":
            # Saturday = 6, Sunday = 7 in isoweekday
            return dt.isoweekday() >= 6

        return False

    def _compare(
        self,
        left: Any,
        operator: str,
        right: Union[int, float, str],
    ) -> bool:
        """Compare two values using the given operator.

        Args:
            left: The left operand (field value from row).
            operator: The comparison operator (>, <, >=, <=, ==, !=).
            right: The right operand (literal value from condition).

        Returns:
            True if the comparison is true, False otherwise.
        """
        if operator == ">":
            return left > right  # type: ignore[no-any-return]
        if operator == "<":
            return left < right  # type: ignore[no-any-return]
        if operator == ">=":
            return left >= right  # type: ignore[no-any-return]
        if operator == "<=":
            return left <= right  # type: ignore[no-any-return]
        if operator == "==":
            return left == right  # type: ignore[no-any-return]
        if operator == "!=":
            return left != right  # type: ignore[no-any-return]

        # Unknown operator
        return False

    # =========================================================================
    # File I/O Operations
    # =========================================================================

    def _expand_env_vars(self, text: str) -> str:
        """Expand ${ENV_VAR} placeholders in text.

        Args:
            text: Text containing ${VAR} placeholders.

        Returns:
            Text with placeholders replaced by environment variable values.

        Raises:
            RuntimeError: If an environment variable is not set.
        """
        pattern = r"\$\{([^}]+)\}"

        def replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is None:
                raise RuntimeError(f"Environment variable '{var_name}' is not set")
            return value

        return re.sub(pattern, replace, text)

    def _execute_read(self, read_op: Read) -> None:
        """Execute a READ operation.

        Loads data from JSON or CSV file into environment.

        Args:
            read_op: The Read AST node to execute.

        Raises:
            RuntimeError: If file not found or format error.
        """
        path_str = self._expand_env_vars(str(read_op.path.value))
        target_name = read_op.target.name
        file_format = read_op.format

        path = Path(path_str)
        if not path.exists():
            raise RuntimeError(f"File not found: {path_str}")

        try:
            if file_format == "JSON":
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                # Ensure data is a list of dicts
                if isinstance(data, dict):
                    data = [data]
                elif not isinstance(data, list):
                    raise RuntimeError(f"JSON file must contain an array or object: {path_str}")
            elif file_format == "CSV":
                with open(path, encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                # Convert numeric strings to numbers
                for row in data:
                    for key, value in row.items():
                        if value is not None:
                            try:
                                if "." in value:
                                    row[key] = float(value)
                                else:
                                    row[key] = int(value)
                            except (ValueError, TypeError):
                                pass  # Keep as string
            else:
                raise RuntimeError(f"Unknown file format: {file_format}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in file '{path_str}': {e}") from e
        except csv.Error as e:
            raise RuntimeError(f"Invalid CSV in file '{path_str}': {e}") from e

        self._environment[target_name] = data

    def _execute_write(self, write_op: Write) -> None:
        """Execute a WRITE operation.

        Saves data from environment to JSON or CSV file.

        Args:
            write_op: The Write AST node to execute.

        Raises:
            RuntimeError: If source not found or write error.
        """
        source_name = write_op.source.name
        path_str = self._expand_env_vars(str(write_op.path.value))
        file_format = write_op.format

        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found in environment")

        data = self._environment[source_name]
        path = Path(path_str)

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if file_format == "JSON":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            elif file_format == "CSV":
                if not data:
                    # Write empty file
                    with open(path, "w", encoding="utf-8", newline="") as f:
                        pass
                else:
                    fieldnames = list(data[0].keys())
                    with open(path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
            else:
                raise RuntimeError(f"Unknown file format: {file_format}")
        except OSError as e:
            raise RuntimeError(f"Failed to write file '{path_str}': {e}") from e

    # =========================================================================
    # HTTP Operations
    # =========================================================================

    def _object_literal_to_dict(self, obj: ObjectLiteral) -> dict[str, Any]:
        """Convert an ObjectLiteral AST node to a Python dict.

        Args:
            obj: The ObjectLiteral node.

        Returns:
            A Python dictionary.
        """
        result: dict[str, Any] = {}
        for key, value in obj.pairs:
            # Expand env vars in string values
            if isinstance(value, str):
                value = self._expand_env_vars(value)
            result[key] = value
        return result

    def _execute_fetch(self, fetch_op: Fetch) -> None:
        """Execute a FETCH operation.

        Makes HTTP request and stores response in environment.

        Args:
            fetch_op: The Fetch AST node to execute.

        Raises:
            RuntimeError: If HTTP request fails.
        """
        url = self._expand_env_vars(str(fetch_op.url.value))
        method = fetch_op.method
        target_name = fetch_op.target.name

        headers: dict[str, Any] = {}
        if fetch_op.headers:
            headers = self._object_literal_to_dict(fetch_op.headers)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
            )

            # Parse response body
            try:
                body = response.json()
            except json.JSONDecodeError:
                body = response.text

            # Store response as structured data
            result: dict[str, Any] = {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": body,
            }

            # If body is a list, store it directly for easier pipeline use
            if isinstance(body, list):
                self._environment[target_name] = body
            else:
                self._environment[target_name] = [result]

        except requests.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {e}") from e

    def _execute_post(self, post_op: Post) -> None:
        """Execute a POST operation.

        Sends HTTP POST request with body data.

        Args:
            post_op: The Post AST node to execute.

        Raises:
            RuntimeError: If HTTP request fails.
        """
        url = self._expand_env_vars(str(post_op.url.value))
        target_name = post_op.target.name

        # Get body data
        body_data: Any
        if isinstance(post_op.body, ObjectLiteral):
            body_data = self._object_literal_to_dict(post_op.body)
        else:
            # Variable reference
            var_name = post_op.body.name
            if var_name not in self._environment:
                raise RuntimeError(f"Body variable '{var_name}' not found in environment")
            body_data = self._environment[var_name]

        headers: dict[str, Any] = {"Content-Type": "application/json"}
        if post_op.headers:
            headers.update(self._object_literal_to_dict(post_op.headers))

        try:
            response = requests.post(
                url=url,
                json=body_data,
                headers=headers,
                timeout=30,
            )

            # Parse response body
            try:
                body = response.json()
            except json.JSONDecodeError:
                body = response.text

            # Store response as structured data
            result: dict[str, Any] = {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": body,
            }

            self._environment[target_name] = [result]

        except requests.RequestException as e:
            raise RuntimeError(f"HTTP POST request failed: {e}") from e

    # =========================================================================
    # New Operations (Join, Rename, Drop, Union, Slice, AddColumn)
    # =========================================================================

    def _execute_join(self, join_op: Join) -> None:
        """Execute a JOIN operation.

        Performs inner join between two tables on matching keys.

        Args:
            join_op: The Join AST node to execute.

        Raises:
            RuntimeError: If source tables not found.
        """
        left_name = join_op.left.name
        right_name = join_op.right.name
        target_name = join_op.target.name
        condition = join_op.condition

        # Get source tables
        if left_name not in self._environment:
            raise RuntimeError(f"Left table '{left_name}' not found")
        if right_name not in self._environment:
            raise RuntimeError(f"Right table '{right_name}' not found")

        left_data = self._environment[left_name]
        right_data = self._environment[right_name]

        left_key = condition.left_field
        right_key = condition.right_field

        # Build index on right table for efficient lookup
        right_index: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for row in right_data:
            key_value = row.get(right_key)
            if key_value is not None:
                right_index[key_value].append(row)

        # Perform inner join
        result = []
        for left_row in left_data:
            left_key_value = left_row.get(left_key)
            if left_key_value is not None and left_key_value in right_index:
                for right_row in right_index[left_key_value]:
                    # Merge rows - left takes precedence on conflicts
                    merged = dict(right_row)
                    merged.update(left_row)
                    result.append(merged)

        self._environment[target_name] = result

    def _execute_left_join(self, join_op: LeftJoin) -> None:
        """Execute a LEFT_JOIN operation.

        Performs left outer join between two tables.

        Args:
            join_op: The LeftJoin AST node to execute.

        Raises:
            RuntimeError: If source tables not found.
        """
        left_name = join_op.left.name
        right_name = join_op.right.name
        target_name = join_op.target.name
        condition = join_op.condition

        # Get source tables
        if left_name not in self._environment:
            raise RuntimeError(f"Left table '{left_name}' not found")
        if right_name not in self._environment:
            raise RuntimeError(f"Right table '{right_name}' not found")

        left_data = self._environment[left_name]
        right_data = self._environment[right_name]

        left_key = condition.left_field
        right_key = condition.right_field

        # Build index on right table
        right_index: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for row in right_data:
            key_value = row.get(right_key)
            if key_value is not None:
                right_index[key_value].append(row)

        # Get all keys from right table for null filling
        right_keys = set()
        if right_data:
            right_keys = set(right_data[0].keys())

        # Perform left join
        result = []
        for left_row in left_data:
            left_key_value = left_row.get(left_key)
            if left_key_value is not None and left_key_value in right_index:
                for right_row in right_index[left_key_value]:
                    merged = dict(right_row)
                    merged.update(left_row)
                    result.append(merged)
            else:
                # No match - include left row with null right columns
                merged = {k: None for k in right_keys}
                merged.update(left_row)
                result.append(merged)

        self._environment[target_name] = result

    def _execute_rename(self, rename_op: Rename) -> None:
        """Execute a RENAME operation.

        Renames columns in a table.

        Args:
            rename_op: The Rename AST node to execute.

        Raises:
            RuntimeError: If source table not found.
        """
        source_name = rename_op.source.name
        target_name = rename_op.target.name

        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found")

        source_data = self._environment[source_name]

        # Build rename mapping
        rename_map = {r.old_name.name: r.new_name.name for r in rename_op.renames}

        # Apply renames
        result = []
        for row in source_data:
            new_row = {}
            for key, value in row.items():
                new_key = rename_map.get(key, key)
                new_row[new_key] = value
            result.append(new_row)

        self._environment[target_name] = result

    def _execute_drop(self, drop_op: Drop) -> None:
        """Execute a DROP operation.

        Removes specified columns from a table.

        Args:
            drop_op: The Drop AST node to execute.

        Raises:
            RuntimeError: If source table not found.
        """
        source_name = drop_op.source.name
        target_name = drop_op.target.name
        columns_to_drop = {col.name for col in drop_op.columns}

        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found")

        source_data = self._environment[source_name]

        # Remove specified columns
        result = []
        for row in source_data:
            new_row = {k: v for k, v in row.items() if k not in columns_to_drop}
            result.append(new_row)

        self._environment[target_name] = result

    def _execute_union(self, union_op: UnionOp) -> None:
        """Execute a UNION operation.

        Combines two tables, optionally removing duplicates.

        Args:
            union_op: The Union AST node to execute.

        Raises:
            RuntimeError: If source tables not found.
        """
        left_name = union_op.left.name
        right_name = union_op.right.name
        target_name = union_op.target.name

        if left_name not in self._environment:
            raise RuntimeError(f"Left table '{left_name}' not found")
        if right_name not in self._environment:
            raise RuntimeError(f"Right table '{right_name}' not found")

        left_data = self._environment[left_name]
        right_data = self._environment[right_name]

        if union_op.all:
            # UNION ALL - keep all rows including duplicates
            result = left_data + right_data
        else:
            # UNION - remove duplicates
            seen: set[tuple[tuple[str, Any], ...]] = set()
            result = []
            for row in left_data + right_data:
                # Create hashable key from row
                row_key = tuple(sorted(row.items()))
                if row_key not in seen:
                    seen.add(row_key)
                    result.append(row)

        self._environment[target_name] = result

    def _execute_slice(self, slice_op: Slice) -> None:
        """Execute a SLICE operation.

        Extracts a range of rows from a table.

        Args:
            slice_op: The Slice AST node to execute.

        Raises:
            RuntimeError: If source table not found.
        """
        source_name = slice_op.source.name
        target_name = slice_op.target.name
        start = slice_op.start
        end = slice_op.end

        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found")

        source_data = self._environment[source_name]
        result = source_data[start:end]

        self._environment[target_name] = result

    def _execute_add_column(self, add_col_op: AddColumn) -> None:
        """Execute an ADD_COLUMN operation.

        Adds a new column with a default value to all rows.

        Args:
            add_col_op: The AddColumn AST node to execute.

        Raises:
            RuntimeError: If source table not found.
        """
        source_name = add_col_op.source.name
        target_name = add_col_op.target.name
        column_name = add_col_op.column_name.name
        default_value = add_col_op.default_value

        if source_name not in self._environment:
            raise RuntimeError(f"Source '{source_name}' not found")

        source_data = self._environment[source_name]

        # Add column to each row
        result = []
        for row in source_data:
            new_row = dict(row)
            new_row[column_name] = self._evaluate_arith(row, default_value)
            result.append(new_row)

        self._environment[target_name] = result

    # =========================================================================
    # Print and Log Statements
    # =========================================================================

    def _execute_print(self, print_stmt: PrintStatement) -> None:
        """Execute a PRINT statement.

        Outputs value to stdout.

        Args:
            print_stmt: The PrintStatement AST node to execute.
        """
        # Evaluate the expression using scalar context
        row = dict(self._scalars)
        result = self._evaluate_arith(row, print_stmt.value)

        # Handle table data specially
        if isinstance(result, list):
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result)

    def _execute_log(self, log_stmt: LogStatement) -> None:
        """Execute a LOG statement.

        Outputs value with log level to stderr.

        Args:
            log_stmt: The LogStatement AST node to execute.
        """
        import sys

        level = log_stmt.level

        # Evaluate the expression using scalar context
        row = dict(self._scalars)
        result = self._evaluate_arith(row, log_stmt.value)

        # Handle table data specially
        if isinstance(result, list):
            output = json.dumps(result, default=str)
        else:
            output = str(result)

        print(f"[{level}] {output}", file=sys.stderr)

    # =========================================================================
    # Math Functions
    # =========================================================================

    def _evaluate_math_func(self, row: dict[str, Any], func: MathFunc) -> Any:
        """Evaluate a math function against a row.

        Args:
            row: The row data.
            func: The MathFunc AST node.

        Returns:
            The computed value.
        """
        import math

        fname = func.func_name
        args = [self._evaluate_arith(row, arg) for arg in func.args]

        if fname == "ABS":
            return abs(args[0]) if args[0] is not None else None

        if fname == "ROUND":
            if args[0] is None:
                return None
            decimals = int(args[1]) if len(args) > 1 else 0
            return round(args[0], decimals)

        if fname == "FLOOR":
            return math.floor(args[0]) if args[0] is not None else None

        if fname == "CEIL":
            return math.ceil(args[0]) if args[0] is not None else None

        if fname == "MOD":
            if args[0] is None or args[1] is None:
                return None
            if args[1] == 0:
                raise RuntimeError("Modulo by zero")
            return args[0] % args[1]

        if fname == "POWER":
            if args[0] is None or args[1] is None:
                return None
            return args[0] ** args[1]

        if fname == "SQRT":
            if args[0] is None:
                return None
            if args[0] < 0:
                raise RuntimeError("Cannot compute square root of negative number")
            return math.sqrt(args[0])

        if fname == "SIGN":
            if args[0] is None:
                return None
            if args[0] > 0:
                return 1
            if args[0] < 0:
                return -1
            return 0

        if fname == "TRUNC":
            return math.trunc(args[0]) if args[0] is not None else None

        if fname == "MIN_VAL":
            valid_args = [a for a in args if a is not None]
            return min(valid_args) if valid_args else None

        if fname == "MAX_VAL":
            valid_args = [a for a in args if a is not None]
            return max(valid_args) if valid_args else None

        raise RuntimeError(f"Unknown math function: {fname}")

    # =========================================================================
    # Type Functions
    # =========================================================================

    def _evaluate_type_func(self, row: dict[str, Any], func: TypeFunc) -> Any:
        """Evaluate a type conversion function against a row.

        Args:
            row: The row data.
            func: The TypeFunc AST node.

        Returns:
            The converted value.
        """
        fname = func.func_name
        value = self._evaluate_arith(row, func.arg)

        if value is None:
            return None

        if fname == "TO_INT":
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None

        if fname == "TO_STRING":
            return str(value)

        if fname == "TO_DECIMAL":
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        if fname == "TO_BOOL":
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return value != 0
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1")
            return bool(value)

        raise RuntimeError(f"Unknown type function: {fname}")

    # =========================================================================
    # Type Check Functions
    # =========================================================================

    def _evaluate_type_check(self, row: dict[str, Any], check: TypeCheck) -> bool:
        """Evaluate a type check condition against a row.

        Args:
            row: The row data.
            check: The TypeCheck AST node.

        Returns:
            True if the type check passes, False otherwise.
        """
        fname = check.func_name
        value = self._evaluate_arith(row, check.arg)

        if fname == "IS_INT":
            return isinstance(value, int) and not isinstance(value, bool)

        if fname == "IS_STRING":
            return isinstance(value, str)

        if fname == "IS_DECIMAL":
            return isinstance(value, float)

        if fname == "IS_BOOL":
            return isinstance(value, bool)

        if fname == "IS_LIST":
            return isinstance(value, list)

        if fname == "IS_DATE":
            return isinstance(value, (date, datetime))

        if fname == "IS_EMPTY":
            if value is None:
                return True
            if isinstance(value, str):
                return value == ""
            if isinstance(value, (list, dict)):
                return len(value) == 0
            return False

        if fname == "IS_NUMERIC":
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        return False

    # =========================================================================
    # List Functions
    # =========================================================================

    def _evaluate_list_func(self, row: dict[str, Any], func: ListFunc) -> Any:
        """Evaluate a list function against a row.

        Args:
            row: The row data.
            func: The ListFunc AST node.

        Returns:
            The computed value.
        """
        fname = func.func_name
        args = [self._evaluate_arith(row, arg) for arg in func.args]

        if fname == "FIRST":
            lst = args[0]
            if lst is None or not isinstance(lst, list) or len(lst) == 0:
                return None
            return lst[0]

        if fname == "LAST":
            lst = args[0]
            if lst is None or not isinstance(lst, list) or len(lst) == 0:
                return None
            return lst[-1]

        if fname == "NTH":
            lst = args[0]
            index = int(args[1]) if args[1] is not None else 0
            if lst is None or not isinstance(lst, list):
                return None
            if index < 0 or index >= len(lst):
                return None
            return lst[index]

        if fname == "FLATTEN":
            lst = args[0]
            if lst is None or not isinstance(lst, list):
                return []
            result = []
            for item in lst:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result

        if fname == "UNIQUE":
            lst = args[0]
            if lst is None or not isinstance(lst, list):
                return []
            seen: set[Any] = set()
            result = []
            for item in lst:
                # Handle unhashable types by converting to string
                try:
                    key = item if not isinstance(item, dict) else json.dumps(item, sort_keys=True)
                except TypeError:
                    key = str(item)
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            return result

        if fname == "LIST_CONTAINS":
            lst = args[0]
            value = args[1]
            if lst is None or not isinstance(lst, list):
                return False
            return value in lst

        if fname == "RANGE":
            start = int(args[0]) if args[0] is not None else 0
            end = int(args[1]) if args[1] is not None else 0
            step = int(args[2]) if len(args) > 2 and args[2] is not None else 1
            if step == 0:
                raise RuntimeError("RANGE step cannot be zero")
            return list(range(start, end, step))

        raise RuntimeError(f"Unknown list function: {fname}")

    # =========================================================================
    # If Expression and NullIf
    # =========================================================================

    def _evaluate_if_expr(self, row: dict[str, Any], expr: IfExpr) -> Any:
        """Evaluate an IF expression.

        Args:
            row: The row data.
            expr: The IfExpr AST node.

        Returns:
            The then_value if condition is true, else_value otherwise.
        """
        condition_result = self._evaluate_condition(row, expr.condition)
        if condition_result:
            return self._evaluate_arith(row, expr.then_value)
        return self._evaluate_arith(row, expr.else_value)

    def _evaluate_nullif(self, row: dict[str, Any], expr: NullIf) -> Any:
        """Evaluate a NULLIF expression.

        Returns NULL if value equals compare_value, otherwise returns value.

        Args:
            row: The row data.
            expr: The NullIf AST node.

        Returns:
            NULL if values are equal, otherwise the value.
        """
        value = self._evaluate_arith(row, expr.value)
        compare_value = self._evaluate_arith(row, expr.compare_value)
        if value == compare_value:
            return None
        return value
