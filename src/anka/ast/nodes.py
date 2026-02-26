"""Immutable AST node definitions for Anka.

All nodes are frozen dataclasses with source location tracking.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass(frozen=True)
class SourceLocation:
    """Source code location for error reporting.

    Attributes:
        line: 1-indexed line number.
        column: 1-indexed column number.
        end_line: Optional ending line number.
        end_column: Optional ending column number.
    """

    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __str__(self) -> str:
        """Format as line:column."""
        return f"{self.line}:{self.column}"


@dataclass(frozen=True)
class ASTNode:
    """Base class for all AST nodes.

    All nodes must have a source location for error reporting.
    """

    source_location: SourceLocation


@dataclass(frozen=True)
class Identifier(ASTNode):
    """An identifier (variable name, field name, etc.).

    Attributes:
        name: The identifier string.
    """

    name: str


@dataclass(frozen=True)
class TypeName(ASTNode):
    """A primitive type name (INT, STRING, DECIMAL, BOOL).

    Attributes:
        name: The type name string.
    """

    name: str


@dataclass(frozen=True)
class Literal(ASTNode):
    """A literal value (number, string, or boolean).

    Attributes:
        value: The literal value.
        literal_type: The type of literal ("NUMBER", "STRING", or "BOOL").
    """

    value: Union[int, float, str, bool]
    literal_type: str


@dataclass(frozen=True)
class BinaryOp(ASTNode):
    """A binary comparison operation.

    Attributes:
        left: The left operand (field name).
        operator: The comparison operator (>, <, >=, <=, ==, !=).
        right: The right operand (literal value).
    """

    left: Identifier
    operator: str
    right: Literal


@dataclass(frozen=True)
class IsNullCheck(ASTNode):
    """IS_NULL or IS_NOT_NULL check.

    Attributes:
        operand: The field to check.
        negated: True for IS_NOT_NULL, False for IS_NULL.
    """

    operand: Identifier
    negated: bool


@dataclass(frozen=True)
class InCheck(ASTNode):
    """IN (value1, value2, ...) check.

    Attributes:
        operand: The field to check.
        values: Sequence of values to check against.
    """

    operand: Identifier
    values: Sequence[Literal]


@dataclass(frozen=True)
class BetweenCheck(ASTNode):
    """BETWEEN low AND high check.

    Attributes:
        operand: The field to check.
        low: Lower bound (inclusive).
        high: Upper bound (inclusive).
    """

    operand: Identifier
    low: Literal
    high: Literal


# Forward references for recursive types
Condition = Union[
    BinaryOp, IsNullCheck, InCheck, BetweenCheck, "StringCheck", "DateCheck",
    "NotExpr", "AndExpr", "OrExpr", "TypeCheck"
]


@dataclass(frozen=True)
class NotExpr(ASTNode):
    """NOT expression.

    Attributes:
        operand: The condition to negate.
    """

    operand: Condition


@dataclass(frozen=True)
class AndExpr(ASTNode):
    """AND expression (conjunction of conditions).

    Attributes:
        conditions: Sequence of conditions to AND together.
    """

    conditions: Sequence[Condition]


@dataclass(frozen=True)
class OrExpr(ASTNode):
    """OR expression (disjunction of conditions).

    Attributes:
        conditions: Sequence of conditions to OR together.
    """

    conditions: Sequence[Condition]


@dataclass(frozen=True)
class Coalesce(ASTNode):
    """COALESCE(field, default) expression.

    Attributes:
        field: The field to check for null.
        default: The default value if field is null (can be Literal or Identifier).
    """

    field: Identifier
    default: "Literal | Identifier"


@dataclass(frozen=True)
class StringFunc(ASTNode):
    """String function call.

    Supports: UPPER, LOWER, TRIM, LTRIM, RTRIM, LENGTH, REVERSE,
              SUBSTRING, LEFT, RIGHT, INDEX_OF, REPLACE, REPLACE_ALL,
              PAD_LEFT, PAD_RIGHT, REPEAT, CONCAT

    Attributes:
        func_name: The function name.
        args: Arguments to the function (can be nested expressions).
    """

    func_name: str
    args: Sequence[Union["ArithOperand", Identifier, Literal]]


@dataclass(frozen=True)
class MathFunc(ASTNode):
    """Math function call.

    Supports: ABS, ROUND, FLOOR, CEIL, MOD, POWER, SQRT, SIGN, TRUNC, MIN_VAL, MAX_VAL

    Attributes:
        func_name: The function name.
        args: Arguments to the function.
    """

    func_name: str
    args: Sequence[Union["ArithOperand", Identifier, Literal]]


@dataclass(frozen=True)
class TypeFunc(ASTNode):
    """Type casting function call.

    Supports: TO_INT, TO_STRING, TO_DECIMAL, TO_BOOL

    Attributes:
        func_name: The function name.
        arg: The value to convert.
    """

    func_name: str
    arg: Union["ArithOperand", Identifier, Literal]


@dataclass(frozen=True)
class TypeCheck(ASTNode):
    """Type checking expression.

    Supports: IS_INT, IS_STRING, IS_DECIMAL, IS_BOOL, IS_LIST, IS_DATE, IS_EMPTY, IS_NUMERIC

    Attributes:
        func_name: The function name.
        arg: The value to check.
    """

    func_name: str
    arg: Union["ArithOperand", Identifier, Literal]


@dataclass(frozen=True)
class ListFunc(ASTNode):
    """List function call.

    Supports: FIRST, LAST, NTH, FLATTEN, UNIQUE, LIST_CONTAINS, RANGE

    Attributes:
        func_name: The function name.
        args: Arguments to the function.
    """

    func_name: str
    args: Sequence[Union["ArithOperand", Identifier, Literal]]


@dataclass(frozen=True)
class IfExpr(ASTNode):
    """Inline IF expression.

    IF(condition, then_value, else_value)

    Attributes:
        condition: The condition to evaluate.
        then_value: Value if condition is true.
        else_value: Value if condition is false.
    """

    condition: "Condition"
    then_value: Union["ArithOperand", Identifier, Literal]
    else_value: Union["ArithOperand", Identifier, Literal]


@dataclass(frozen=True)
class NullIf(ASTNode):
    """NULLIF expression - returns null if values are equal.

    NULLIF(value, compare_value)

    Attributes:
        value: The value to check.
        compare_value: The value to compare against.
    """

    value: Union["ArithOperand", Identifier, Literal]
    compare_value: Union["ArithOperand", Identifier, Literal]


@dataclass(frozen=True)
class StringCheck(ASTNode):
    """String boolean check for WHERE clause.

    Supports: CONTAINS, STARTS_WITH, ENDS_WITH, MATCHES

    Attributes:
        func_name: The check function name.
        field: The field to check.
        pattern: The pattern to match against.
    """

    func_name: str
    field: Identifier
    pattern: Literal


@dataclass(frozen=True)
class DateFunc(ASTNode):
    """Date/time function call.

    Supports: NOW, TODAY, YEAR, MONTH, DAY, HOUR, MINUTE, SECOND,
              DAY_OF_WEEK, WEEK_OF_YEAR, ADD_DAYS, ADD_MONTHS, ADD_YEARS,
              ADD_HOURS, DIFF_DAYS, PARSE_DATE, FORMAT_DATE

    Attributes:
        func_name: The function name.
        args: Arguments to the function (can be nested expressions).
        format_pattern: Optional format pattern for PARSE_DATE, FORMAT_DATE.
    """

    func_name: str
    args: Sequence[Union["ArithOperand", Identifier, Literal]]
    format_pattern: Optional[str] = None


@dataclass(frozen=True)
class DateCheck(ASTNode):
    """Date boolean check for WHERE clause.

    Supports: IS_BEFORE, IS_AFTER, IS_WEEKEND

    Attributes:
        func_name: The check function name.
        field: The field to check.
        compare_value: The value to compare against (for IS_BEFORE, IS_AFTER).
    """

    func_name: str
    field: Identifier
    compare_value: Optional[Union["ArithOperand", Identifier, Literal]] = None


# Type alias for arithmetic expression operands
ArithOperand = Union[
    "ArithmeticOp", Identifier, Literal, Coalesce, StringFunc, DateFunc,
    MathFunc, TypeFunc, ListFunc, IfExpr, NullIf
]


@dataclass(frozen=True)
class ArithmeticOp(ASTNode):
    """An arithmetic binary operation (+, -, *, /).

    Attributes:
        left: Left operand (ArithmeticOp, Identifier, or Literal).
        operator: The operator (+, -, *, /).
        right: Right operand (ArithmeticOp, Identifier, or Literal).
    """

    left: ArithOperand
    operator: str
    right: ArithOperand


@dataclass(frozen=True)
class Filter(ASTNode):
    """A FILTER operation.

    Attributes:
        source: The source table identifier.
        condition: The filter condition (binary comparison).
        target: The target table identifier.
    """

    source: Identifier
    condition: BinaryOp
    target: Identifier


@dataclass(frozen=True)
class Select(ASTNode):
    """A SELECT operation.

    Attributes:
        columns: Sequence of column names to select.
        source: The source table identifier.
        target: The target table identifier.
    """

    columns: Sequence[Identifier]
    source: Identifier
    target: Identifier


# Type alias for all operation types
Operation = Union[
    Filter, "Select", "Map", "Sort", "Limit", "Skip", "Distinct", "Aggregate",
    "Read", "Write", "Fetch", "Post",
    "Join", "LeftJoin", "Rename", "Drop", "UnionOp", "Slice", "AddColumn"
]


@dataclass(frozen=True)
class Step(ASTNode):
    """A named STEP in a pipeline.

    Attributes:
        name: The step name.
        operation: The operation to perform.
    """

    name: Identifier
    operation: Operation


@dataclass(frozen=True)
class FieldDef(ASTNode):
    """A field definition in a table type.

    Attributes:
        name: The field name.
        type_name: The field's type.
    """

    name: Identifier
    type_name: TypeName


@dataclass(frozen=True)
class TableType(ASTNode):
    """A TABLE type with named, typed fields.

    Attributes:
        fields: Sequence of field definitions.
    """

    fields: Sequence[FieldDef] = field(default_factory=tuple)


@dataclass(frozen=True)
class Input(ASTNode):
    """An INPUT declaration in a pipeline.

    Attributes:
        name: The input variable name.
        type_expr: The input's type (currently always TableType).
    """

    name: Identifier
    type_expr: TableType


@dataclass(frozen=True)
class Output(ASTNode):
    """An OUTPUT declaration in a pipeline.

    Attributes:
        name: The output variable name.
    """

    name: Identifier


@dataclass(frozen=True)
class Map(ASTNode):
    """A MAP operation that adds a computed column.

    Attributes:
        source: The source table identifier.
        new_column: Name of the new column to create.
        expression: The arithmetic expression to compute.
        target: The target table identifier.
    """

    source: Identifier
    new_column: Identifier
    expression: ArithOperand
    target: Identifier


@dataclass(frozen=True)
class Sort(ASTNode):
    """A SORT operation that orders rows by a column.

    Attributes:
        source: The source table identifier.
        key: The column to sort by.
        descending: True for DESC, False for ASC.
        nulls_last: None for default, True for NULLS_LAST, False for NULLS_FIRST.
        target: The target table identifier.
    """

    source: Identifier
    key: Identifier
    descending: bool
    nulls_last: Optional[bool]
    target: Identifier


@dataclass(frozen=True)
class Limit(ASTNode):
    """A LIMIT operation that takes the first N rows.

    Attributes:
        source: The source table identifier.
        count: Number of rows to take.
        target: The target table identifier.
    """

    source: Identifier
    count: int
    target: Identifier


@dataclass(frozen=True)
class Skip(ASTNode):
    """A SKIP operation that skips the first N rows.

    Attributes:
        source: The source table identifier.
        count: Number of rows to skip.
        target: The target table identifier.
    """

    source: Identifier
    count: int
    target: Identifier


@dataclass(frozen=True)
class Distinct(ASTNode):
    """A DISTINCT operation that removes duplicate rows by keys.

    Attributes:
        source: The source table identifier.
        keys: Columns to use for uniqueness.
        target: The target table identifier.
    """

    source: Identifier
    keys: Sequence[Identifier]
    target: Identifier


@dataclass(frozen=True)
class AggFunc(ASTNode):
    """An aggregate function (COUNT, SUM, AVG, MIN, MAX).

    Attributes:
        func_name: The function name.
        column: The column to aggregate (None for COUNT()).
    """

    func_name: str
    column: Optional[Identifier]


@dataclass(frozen=True)
class AggExpr(ASTNode):
    """An aggregate expression with alias.

    Attributes:
        func: The aggregate function.
        alias: The output column name.
    """

    func: AggFunc
    alias: Identifier


@dataclass(frozen=True)
class Aggregate(ASTNode):
    """An AGGREGATE operation with optional GROUP_BY.

    Attributes:
        source: The source table identifier.
        group_by: Columns to group by (None for no grouping).
        computations: Aggregate expressions to compute.
        target: The target table identifier.
    """

    source: Identifier
    group_by: Optional[Sequence[Identifier]]
    computations: Sequence[AggExpr]
    target: Identifier


@dataclass(frozen=True)
class Pipeline(ASTNode):
    """A complete PIPELINE declaration.

    Attributes:
        name: The pipeline name.
        inputs: Sequence of input declarations.
        steps: Sequence of step declarations (deprecated, use body).
        body: Sequence of pipeline body items (steps and statements).
        outputs: The output declaration.
    """

    name: Identifier
    inputs: Sequence[Input] = field(default_factory=tuple)
    steps: Sequence[Step] = field(default_factory=tuple)
    body: Sequence[Any] = field(default_factory=tuple)  # PipelineBodyItem defined later
    outputs: Optional[Output] = None


# =============================================================================
# File I/O Operations
# =============================================================================


@dataclass(frozen=True)
class ObjectLiteral(ASTNode):
    """An object literal for headers or POST body.

    Attributes:
        pairs: Sequence of (key, value) tuples.
    """

    pairs: Sequence[tuple[str, Any]]


@dataclass(frozen=True)
class Read(ASTNode):
    """A READ operation to load data from a file.

    Attributes:
        path: Path to the file (may contain ${ENV_VAR}).
        format: File format ("JSON" or "CSV").
        target: The target variable name.
    """

    path: Literal
    format: str
    target: Identifier


@dataclass(frozen=True)
class Write(ASTNode):
    """A WRITE operation to save data to a file.

    Attributes:
        source: The source variable name.
        path: Path to the output file.
        format: File format ("JSON" or "CSV").
    """

    source: Identifier
    path: Literal
    format: str


# =============================================================================
# HTTP Operations
# =============================================================================


@dataclass(frozen=True)
class Fetch(ASTNode):
    """A FETCH operation to make HTTP requests.

    Attributes:
        url: The URL to fetch (may contain ${ENV_VAR}).
        method: HTTP method ("GET", "POST", "PUT", "DELETE").
        headers: Optional headers object literal.
        target: The target variable name.
    """

    url: Literal
    method: str
    headers: Optional[ObjectLiteral]
    target: Identifier


@dataclass(frozen=True)
class Post(ASTNode):
    """A POST operation to send data via HTTP.

    Attributes:
        url: The URL to post to.
        body: The request body (ObjectLiteral or variable reference).
        headers: Optional headers object literal.
        target: The target variable name.
    """

    url: Literal
    body: Union[ObjectLiteral, Identifier]
    headers: Optional[ObjectLiteral]
    target: Identifier


# =============================================================================
# New Operations (JOIN, RENAME, DROP, UNION, SLICE, ADD_COLUMN)
# =============================================================================


@dataclass(frozen=True)
class JoinCondition(ASTNode):
    """A join condition: left_table.left_field == right_table.right_field.

    Attributes:
        left_table: The left table name.
        left_field: The left field name.
        right_table: The right table name.
        right_field: The right field name.
    """

    left_table: str
    left_field: str
    right_table: str
    right_field: str


@dataclass(frozen=True)
class Join(ASTNode):
    """An inner JOIN operation.

    Attributes:
        left: The left table identifier.
        right: The right table identifier.
        condition: The join condition.
        target: The target table identifier.
    """

    left: Identifier
    right: Identifier
    condition: JoinCondition
    target: Identifier


@dataclass(frozen=True)
class LeftJoin(ASTNode):
    """A LEFT JOIN operation.

    Attributes:
        left: The left table identifier.
        right: The right table identifier.
        condition: The join condition.
        target: The target table identifier.
    """

    left: Identifier
    right: Identifier
    condition: JoinCondition
    target: Identifier


@dataclass(frozen=True)
class RenameClause(ASTNode):
    """A single rename clause: old_name AS new_name.

    Attributes:
        old_name: The original column name.
        new_name: The new column name.
    """

    old_name: Identifier
    new_name: Identifier


@dataclass(frozen=True)
class Rename(ASTNode):
    """A RENAME operation to rename columns.

    Attributes:
        source: The source table identifier.
        renames: Sequence of rename clauses.
        target: The target table identifier.
    """

    source: Identifier
    renames: Sequence[RenameClause]
    target: Identifier


@dataclass(frozen=True)
class Drop(ASTNode):
    """A DROP operation to remove columns.

    Attributes:
        source: The source table identifier.
        columns: Columns to drop.
        target: The target table identifier.
    """

    source: Identifier
    columns: Sequence[Identifier]
    target: Identifier


@dataclass(frozen=True)
class UnionOp(ASTNode):
    """A UNION operation to combine tables.

    Attributes:
        left: The left table identifier.
        right: The right table identifier.
        target: The target table identifier.
        all: If True, keep duplicates (UNION_ALL).
    """

    left: Identifier
    right: Identifier
    target: Identifier
    all: bool = False


@dataclass(frozen=True)
class Slice(ASTNode):
    """A SLICE operation for pagination.

    Attributes:
        source: The source table identifier.
        start: Starting index (0-based).
        end: Ending index (exclusive).
        target: The target table identifier.
    """

    source: Identifier
    start: int
    end: int
    target: Identifier


@dataclass(frozen=True)
class AddColumn(ASTNode):
    """An ADD_COLUMN operation to add a column with a default value.

    Attributes:
        source: The source table identifier.
        column_name: The new column name.
        default_value: The default value expression.
        target: The target table identifier.
    """

    source: Identifier
    column_name: Identifier
    default_value: ArithOperand
    target: Identifier


# =============================================================================
# Print and Log Statements
# =============================================================================


@dataclass(frozen=True)
class PrintStatement(ASTNode):
    """A PRINT statement for output.

    Attributes:
        value: The value to print (string, variable, or expression).
    """

    value: Union[str, Identifier, ArithOperand]


@dataclass(frozen=True)
class LogStatement(ASTNode):
    """A LOG statement for structured logging.

    Attributes:
        level: Log level (INFO, WARN, ERROR, DEBUG).
        value: The value to log (string, variable, or expression).
    """

    level: str
    value: Union[str, Identifier, ArithOperand]


# =============================================================================
# Control Flow Statements
# =============================================================================


@dataclass(frozen=True)
class SetStatement(ASTNode):
    """A SET statement for variable assignment.

    Attributes:
        variable: The variable name to assign to.
        value: The value to assign (can be expression, literal, or var reference).
    """

    variable: Identifier
    value: Union[ArithOperand, Literal, Identifier, bool]


@dataclass(frozen=True)
class IfStatement(ASTNode):
    """An IF/ELSE conditional statement.

    Attributes:
        condition: The condition to evaluate.
        then_body: Body to execute if condition is true.
        else_body: Body to execute if condition is false (None if no else).
    """

    condition: Condition
    then_body: Sequence["PipelineBodyItem"]
    else_body: Optional[Sequence["PipelineBodyItem"]] = None


@dataclass(frozen=True)
class ForEachStatement(ASTNode):
    """A FOR_EACH loop statement.

    Attributes:
        item_var: Variable name for each item.
        collection: Collection variable to iterate over.
        body: Body to execute for each item.
    """

    item_var: Identifier
    collection: Identifier
    body: Sequence["PipelineBodyItem"]


@dataclass(frozen=True)
class WhileStatement(ASTNode):
    """A WHILE loop statement.

    Attributes:
        condition: Condition to evaluate before each iteration.
        body: Body to execute while condition is true.
        max_iterations: Maximum iterations to prevent infinite loops (default 10000).
    """

    condition: Condition
    body: Sequence["PipelineBodyItem"]
    max_iterations: int = 10000


@dataclass(frozen=True)
class TryStatement(ASTNode):
    """A TRY/ON_ERROR error handling statement.

    Attributes:
        try_body: Body to execute in the try block.
        error_body: Body to execute if an error occurs.
    """

    try_body: Sequence["PipelineBodyItem"]
    error_body: Sequence["PipelineBodyItem"]


@dataclass(frozen=True)
class MatchCase(ASTNode):
    """A single CASE in a MATCH statement.

    Attributes:
        value: The value to match against.
        body: Body to execute if matched.
    """

    value: Union[int, float, str, bool]
    body: Sequence["PipelineBodyItem"]


@dataclass(frozen=True)
class MatchStatement(ASTNode):
    """A MATCH pattern matching statement.

    Attributes:
        variable: The variable to match on.
        cases: Sequence of match cases.
        default_body: Body to execute if no case matches (optional).
    """

    variable: Identifier
    cases: Sequence[MatchCase]
    default_body: Optional[Sequence["PipelineBodyItem"]] = None


@dataclass(frozen=True)
class AssertStatement(ASTNode):
    """An ASSERT validation statement.

    Attributes:
        condition: The condition that must be true.
        message: Optional error message if assertion fails.
    """

    condition: Condition
    message: Optional[str] = None


@dataclass(frozen=True)
class ReturnStatement(ASTNode):
    """A RETURN statement for early exit.

    Attributes:
        value: Optional variable name to return.
    """

    value: Optional[Identifier] = None


@dataclass(frozen=True)
class BreakStatement(ASTNode):
    """A BREAK statement to exit a loop early."""

    pass


@dataclass(frozen=True)
class ContinueStatement(ASTNode):
    """A CONTINUE statement to skip to the next loop iteration."""

    pass


@dataclass(frozen=True)
class AppendStatement(ASTNode):
    """An APPEND statement to add data to a collection.

    Attributes:
        source: The data to append.
        target: The collection to append to.
    """

    source: Identifier
    target: Identifier


# Type alias for pipeline body items
PipelineBodyItem = Union[
    Step, SetStatement, IfStatement, ForEachStatement, WhileStatement,
    TryStatement, MatchStatement, AssertStatement, ReturnStatement,
    BreakStatement, ContinueStatement, AppendStatement,
    PrintStatement, LogStatement
]
