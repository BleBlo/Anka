"""Anka parser - transforms source code into AST."""

from pathlib import Path
from typing import Any, Optional, Union, cast

from lark import Lark, Token, Transformer, v_args

from anka.ast.nodes import (
    AddColumn,
    AggExpr,
    AggFunc,
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
    FieldDef,
    Filter,
    ForEachStatement,
    Identifier,
    IfExpr,
    IfStatement,
    InCheck,
    Input,
    IsNullCheck,
    Join,
    JoinCondition,
    LeftJoin,
    Limit,
    ListFunc,
    Literal,
    LogStatement,
    Map,
    MatchCase,
    MatchStatement,
    MathFunc,
    NotExpr,
    NullIf,
    ObjectLiteral,
    OrExpr,
    Output,
    Pipeline,
    Post,
    PrintStatement,
    Read,
    Rename,
    RenameClause,
    ReturnStatement,
    Select,
    SetStatement,
    Skip,
    Slice,
    Sort,
    SourceLocation,
    Step,
    StringCheck,
    StringFunc,
    TableType,
    TryStatement,
    TypeCheck,
    TypeFunc,
    TypeName,
    UnionOp,
    WhileStatement,
    Write,
)

# Type alias for arithmetic operands
ArithOperand = Union[ArithmeticOp, Identifier, Literal]

# Load grammar from file
GRAMMAR_PATH = Path(__file__).parent / "anka.lark"


def _make_location(token: Token) -> SourceLocation:
    """Create a SourceLocation from a Lark token."""
    return SourceLocation(
        line=token.line or 1,
        column=token.column or 1,
    )


def _make_location_from_meta(meta: Any) -> SourceLocation:
    """Create a SourceLocation from Lark tree metadata."""
    return SourceLocation(
        line=getattr(meta, "line", 1),
        column=getattr(meta, "column", 1),
        end_line=getattr(meta, "end_line", None),
        end_column=getattr(meta, "end_column", None),
    )


@v_args(meta=True)
class AnkaTransformer(Transformer[Token, Pipeline]):
    """Transform Lark parse tree into Anka AST nodes."""

    def NAME(self, token: Token) -> Identifier:
        """Transform a NAME token into an Identifier."""
        return Identifier(
            source_location=_make_location(token),
            name=str(token),
        )

    def NUMBER(self, token: Token) -> Token:
        """Pass through NUMBER token for later processing."""
        return token

    def SIGNED_NUMBER(self, token: Token) -> Token:
        """Pass through SIGNED_NUMBER token for later processing."""
        return token

    def QUOTED_STRING(self, token: Token) -> Token:
        """Pass through QUOTED_STRING token for later processing."""
        return token

    # Literal transformers
    def number_literal(self, _meta: Any, children: list[Any]) -> Literal:
        """Transform a number literal."""
        token = children[0]
        value_str = str(token)
        # Parse as float if it has a decimal point, otherwise int
        value: Union[int, float] = float(value_str) if "." in value_str else int(value_str)
        return Literal(
            source_location=_make_location(token),
            value=value,
            literal_type="NUMBER",
        )

    def string_literal(self, _meta: Any, children: list[Any]) -> Literal:
        """Transform a string literal."""
        token = children[0]
        # Remove quotes from the string value
        value = str(token)[1:-1]
        return Literal(
            source_location=_make_location(token),
            value=value,
            literal_type="STRING",
        )

    def true_literal(self, meta: Any, _children: list[Any]) -> Literal:
        """Transform a true literal."""
        return Literal(
            source_location=_make_location_from_meta(meta),
            value=True,
            literal_type="BOOL",
        )

    def false_literal(self, meta: Any, _children: list[Any]) -> Literal:
        """Transform a false literal."""
        return Literal(
            source_location=_make_location_from_meta(meta),
            value=False,
            literal_type="BOOL",
        )

    # Comparison operator transformers
    def gt(self, _meta: Any, _children: list[Any]) -> str:
        """Transform > operator."""
        return ">"

    def lt(self, _meta: Any, _children: list[Any]) -> str:
        """Transform < operator."""
        return "<"

    def gte(self, _meta: Any, _children: list[Any]) -> str:
        """Transform >= operator."""
        return ">="

    def lte(self, _meta: Any, _children: list[Any]) -> str:
        """Transform <= operator."""
        return "<="

    def eq(self, _meta: Any, _children: list[Any]) -> str:
        """Transform == operator."""
        return "=="

    def neq(self, _meta: Any, _children: list[Any]) -> str:
        """Transform != operator."""
        return "!="

    def compare_op(self, _meta: Any, children: list[Any]) -> str:
        """Pass through comparison operator."""
        return cast(str, children[0])

    # Arithmetic expression transformers
    def arith_number(self, _meta: Any, children: list[Any]) -> Literal:
        """Transform an arithmetic number literal."""
        token = children[0]
        value_str = str(token)
        value: Union[int, float] = float(value_str) if "." in value_str else int(value_str)
        return Literal(
            source_location=_make_location(token),
            value=value,
            literal_type="NUMBER",
        )

    def arith_name(self, _meta: Any, children: list[Any]) -> Identifier:
        """Transform an arithmetic name (field reference)."""
        return cast(Identifier, children[0])

    def arith_string(self, _meta: Any, children: list[Any]) -> Literal:
        """Transform an arithmetic string literal."""
        token = children[0]
        value = str(token)[1:-1]  # Remove quotes
        return Literal(
            source_location=_make_location(token),
            value=value,
            literal_type="STRING",
        )

    def coalesce_expr(self, meta: Any, children: list[Any]) -> Coalesce:
        """Transform COALESCE expression."""
        field, default = children
        return Coalesce(
            source_location=_make_location_from_meta(meta),
            field=field,
            default=default,
        )

    def coalesce_value(self, _meta: Any, children: list[Any]) -> Literal:
        """Pass through coalesce value (literal)."""
        return cast(Literal, children[0])

    def coalesce_name(self, _meta: Any, children: list[Any]) -> Identifier:
        """Pass through coalesce name (identifier for fallback column)."""
        return cast(Identifier, children[0])

    def upper_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform UPPER function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="UPPER",
            args=(children[0],),
        )

    def lower_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform LOWER function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="LOWER",
            args=(children[0],),
        )

    def trim_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform TRIM function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TRIM",
            args=(children[0],),
        )

    def ltrim_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform LTRIM function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="LTRIM",
            args=(children[0],),
        )

    def rtrim_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform RTRIM function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="RTRIM",
            args=(children[0],),
        )

    def length_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform LENGTH function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="LENGTH",
            args=(children[0],),
        )

    def reverse_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform REVERSE function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="REVERSE",
            args=(children[0],),
        )

    def substring_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform SUBSTRING function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="SUBSTRING",
            args=tuple(children),
        )

    def left_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform LEFT function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="LEFT",
            args=tuple(children),
        )

    def right_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform RIGHT function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="RIGHT",
            args=tuple(children),
        )

    def index_of_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform INDEX_OF function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="INDEX_OF",
            args=tuple(children),
        )

    def replace_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform REPLACE function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="REPLACE",
            args=tuple(children),
        )

    def replace_all_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform REPLACE_ALL function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="REPLACE_ALL",
            args=tuple(children),
        )

    def pad_left_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform PAD_LEFT function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="PAD_LEFT",
            args=tuple(children),
        )

    def pad_right_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform PAD_RIGHT function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="PAD_RIGHT",
            args=tuple(children),
        )

    def repeat_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform REPEAT function."""
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="REPEAT",
            args=tuple(children),
        )

    def concat_func(self, meta: Any, children: list[Any]) -> StringFunc:
        """Transform CONCAT function."""
        args = children[0]  # concat_args returns tuple
        return StringFunc(
            source_location=_make_location_from_meta(meta),
            func_name="CONCAT",
            args=args,
        )

    # String check transformers for WHERE clause
    def contains_check(self, meta: Any, children: list[Any]) -> StringCheck:
        """Transform CONTAINS check."""
        field = children[0]
        pattern_token = children[1]
        pattern_value = str(pattern_token)[1:-1]  # Remove quotes
        pattern = Literal(
            source_location=_make_location(pattern_token),
            value=pattern_value,
            literal_type="STRING",
        )
        return StringCheck(
            source_location=_make_location_from_meta(meta),
            func_name="CONTAINS",
            field=field,
            pattern=pattern,
        )

    def starts_with_check(self, meta: Any, children: list[Any]) -> StringCheck:
        """Transform STARTS_WITH check."""
        field = children[0]
        pattern_token = children[1]
        pattern_value = str(pattern_token)[1:-1]  # Remove quotes
        pattern = Literal(
            source_location=_make_location(pattern_token),
            value=pattern_value,
            literal_type="STRING",
        )
        return StringCheck(
            source_location=_make_location_from_meta(meta),
            func_name="STARTS_WITH",
            field=field,
            pattern=pattern,
        )

    def ends_with_check(self, meta: Any, children: list[Any]) -> StringCheck:
        """Transform ENDS_WITH check."""
        field = children[0]
        pattern_token = children[1]
        pattern_value = str(pattern_token)[1:-1]  # Remove quotes
        pattern = Literal(
            source_location=_make_location(pattern_token),
            value=pattern_value,
            literal_type="STRING",
        )
        return StringCheck(
            source_location=_make_location_from_meta(meta),
            func_name="ENDS_WITH",
            field=field,
            pattern=pattern,
        )

    def matches_check(self, meta: Any, children: list[Any]) -> StringCheck:
        """Transform MATCHES check."""
        field = children[0]
        pattern_token = children[1]
        pattern_value = str(pattern_token)[1:-1]  # Remove quotes
        pattern = Literal(
            source_location=_make_location(pattern_token),
            value=pattern_value,
            literal_type="STRING",
        )
        return StringCheck(
            source_location=_make_location_from_meta(meta),
            func_name="MATCHES",
            field=field,
            pattern=pattern,
        )

    def string_check(self, _meta: Any, children: list[Any]) -> StringCheck:
        """Pass through string check."""
        return cast(StringCheck, children[0])

    # =========================================================================
    # Date/Time function transformers
    # =========================================================================

    def now_func(self, meta: Any, _children: list[Any]) -> DateFunc:
        """Transform NOW function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="NOW",
            args=(),
        )

    def today_func(self, meta: Any, _children: list[Any]) -> DateFunc:
        """Transform TODAY function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TODAY",
            args=(),
        )

    def year_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform YEAR function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="YEAR",
            args=(children[0],),
        )

    def month_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform MONTH function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MONTH",
            args=(children[0],),
        )

    def day_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform DAY function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="DAY",
            args=(children[0],),
        )

    def hour_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform HOUR function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="HOUR",
            args=(children[0],),
        )

    def minute_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform MINUTE function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MINUTE",
            args=(children[0],),
        )

    def second_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform SECOND function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="SECOND",
            args=(children[0],),
        )

    def day_of_week_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform DAY_OF_WEEK function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="DAY_OF_WEEK",
            args=(children[0],),
        )

    def week_of_year_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform WEEK_OF_YEAR function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="WEEK_OF_YEAR",
            args=(children[0],),
        )

    def add_days_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform ADD_DAYS function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="ADD_DAYS",
            args=tuple(children),
        )

    def add_months_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform ADD_MONTHS function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="ADD_MONTHS",
            args=tuple(children),
        )

    def add_years_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform ADD_YEARS function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="ADD_YEARS",
            args=tuple(children),
        )

    def add_hours_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform ADD_HOURS function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="ADD_HOURS",
            args=tuple(children),
        )

    def diff_days_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform DIFF_DAYS function."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="DIFF_DAYS",
            args=tuple(children),
        )

    def parse_date_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform PARSE_DATE function."""
        expr = children[0]
        format_token = children[1]
        format_pattern = str(format_token)[1:-1]  # Remove quotes
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="PARSE_DATE",
            args=(expr,),
            format_pattern=format_pattern,
        )

    def to_date_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform TO_DATE function (simpler PARSE_DATE without explicit format)."""
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TO_DATE",
            args=(children[0],),
        )

    def format_date_func(self, meta: Any, children: list[Any]) -> DateFunc:
        """Transform FORMAT_DATE function."""
        expr = children[0]
        format_token = children[1]
        format_pattern = str(format_token)[1:-1]  # Remove quotes
        return DateFunc(
            source_location=_make_location_from_meta(meta),
            func_name="FORMAT_DATE",
            args=(expr,),
            format_pattern=format_pattern,
        )

    def date_func(self, _meta: Any, children: list[Any]) -> DateFunc:
        """Pass through date function."""
        return cast(DateFunc, children[0])

    # Date check transformers for WHERE clause
    def is_before_check(self, meta: Any, children: list[Any]) -> DateCheck:
        """Transform IS_BEFORE check."""
        field = children[0]
        compare_value = children[1]
        return DateCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_BEFORE",
            field=field,
            compare_value=compare_value,
        )

    def is_after_check(self, meta: Any, children: list[Any]) -> DateCheck:
        """Transform IS_AFTER check."""
        field = children[0]
        compare_value = children[1]
        return DateCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_AFTER",
            field=field,
            compare_value=compare_value,
        )

    def is_weekend_check(self, meta: Any, children: list[Any]) -> DateCheck:
        """Transform IS_WEEKEND check."""
        field = children[0]
        return DateCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_WEEKEND",
            field=field,
        )

    def date_check(self, _meta: Any, children: list[Any]) -> DateCheck:
        """Pass through date check."""
        return cast(DateCheck, children[0])

    # =========================================================================
    # Math function transformers
    # =========================================================================

    def abs_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform ABS function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="ABS",
            args=(children[0],),
        )

    def round_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform ROUND function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="ROUND",
            args=tuple(children),
        )

    def floor_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform FLOOR function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="FLOOR",
            args=(children[0],),
        )

    def ceil_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform CEIL function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="CEIL",
            args=(children[0],),
        )

    def mod_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform MOD function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MOD",
            args=tuple(children),
        )

    def power_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform POWER function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="POWER",
            args=tuple(children),
        )

    def sqrt_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform SQRT function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="SQRT",
            args=(children[0],),
        )

    def sign_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform SIGN function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="SIGN",
            args=(children[0],),
        )

    def trunc_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform TRUNC function."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TRUNC",
            args=(children[0],),
        )

    def min_val_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform MIN_VAL function (scalar min)."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MIN_VAL",
            args=tuple(children),
        )

    def max_val_func(self, meta: Any, children: list[Any]) -> MathFunc:
        """Transform MAX_VAL function (scalar max)."""
        return MathFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MAX_VAL",
            args=tuple(children),
        )

    def math_func(self, _meta: Any, children: list[Any]) -> MathFunc:
        """Pass through math function."""
        return cast(MathFunc, children[0])

    # =========================================================================
    # Type casting function transformers
    # =========================================================================

    def to_int_func(self, meta: Any, children: list[Any]) -> TypeFunc:
        """Transform TO_INT function."""
        return TypeFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TO_INT",
            arg=children[0],
        )

    def to_string_func(self, meta: Any, children: list[Any]) -> TypeFunc:
        """Transform TO_STRING function."""
        return TypeFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TO_STRING",
            arg=children[0],
        )

    def to_decimal_func(self, meta: Any, children: list[Any]) -> TypeFunc:
        """Transform TO_DECIMAL function."""
        return TypeFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TO_DECIMAL",
            arg=children[0],
        )

    def to_bool_func(self, meta: Any, children: list[Any]) -> TypeFunc:
        """Transform TO_BOOL function."""
        return TypeFunc(
            source_location=_make_location_from_meta(meta),
            func_name="TO_BOOL",
            arg=children[0],
        )

    def type_func(self, _meta: Any, children: list[Any]) -> TypeFunc:
        """Pass through type function."""
        return cast(TypeFunc, children[0])

    # =========================================================================
    # Type checking function transformers (for WHERE clause)
    # =========================================================================

    def is_int_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_INT check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_INT",
            arg=children[0],
        )

    def is_string_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_STRING check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_STRING",
            arg=children[0],
        )

    def is_decimal_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_DECIMAL check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_DECIMAL",
            arg=children[0],
        )

    def is_bool_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_BOOL check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_BOOL",
            arg=children[0],
        )

    def is_list_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_LIST check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_LIST",
            arg=children[0],
        )

    def is_date_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_DATE check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_DATE",
            arg=children[0],
        )

    def is_empty_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_EMPTY check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_EMPTY",
            arg=children[0],
        )

    def is_numeric_check(self, meta: Any, children: list[Any]) -> TypeCheck:
        """Transform IS_NUMERIC check."""
        return TypeCheck(
            source_location=_make_location_from_meta(meta),
            func_name="IS_NUMERIC",
            arg=children[0],
        )

    def type_check(self, _meta: Any, children: list[Any]) -> TypeCheck:
        """Pass through type check."""
        return cast(TypeCheck, children[0])

    # =========================================================================
    # List function transformers
    # =========================================================================

    def first_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform FIRST function."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="FIRST",
            args=(children[0],),
        )

    def last_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform LAST function."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="LAST",
            args=(children[0],),
        )

    def nth_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform NTH function."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="NTH",
            args=tuple(children),
        )

    def flatten_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform FLATTEN function."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="FLATTEN",
            args=(children[0],),
        )

    def unique_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform UNIQUE function."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="UNIQUE",
            args=(children[0],),
        )

    def list_contains_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform LIST_CONTAINS function."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="LIST_CONTAINS",
            args=tuple(children),
        )

    def range_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform RANGE function (2 args)."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="RANGE",
            args=tuple(children),
        )

    def range_step_func(self, meta: Any, children: list[Any]) -> ListFunc:
        """Transform RANGE function (3 args with step)."""
        return ListFunc(
            source_location=_make_location_from_meta(meta),
            func_name="RANGE",
            args=tuple(children),
        )

    def list_func(self, _meta: Any, children: list[Any]) -> ListFunc:
        """Pass through list function."""
        return cast(ListFunc, children[0])

    # =========================================================================
    # IF expression and NULLIF transformers
    # =========================================================================

    def if_func(self, meta: Any, children: list[Any]) -> IfExpr:
        """Transform inline IF expression."""
        condition, then_value, else_value = children
        return IfExpr(
            source_location=_make_location_from_meta(meta),
            condition=condition,
            then_value=then_value,
            else_value=else_value,
        )

    def nullif_func(self, meta: Any, children: list[Any]) -> NullIf:
        """Transform NULLIF function."""
        value, compare_value = children
        return NullIf(
            source_location=_make_location_from_meta(meta),
            value=value,
            compare_value=compare_value,
        )

    def if_expr(self, _meta: Any, children: list[Any]) -> Union[IfExpr, NullIf]:
        """Pass through if expression."""
        return cast(Union[IfExpr, NullIf], children[0])

    def concat_args(self, _meta: Any, children: list[Any]) -> tuple[Any, ...]:
        """Transform concat arguments."""
        return tuple(children)

    def concat_name(self, _meta: Any, children: list[Any]) -> Identifier:
        """Transform concat name argument."""
        return cast(Identifier, children[0])

    def concat_string(self, _meta: Any, children: list[Any]) -> Literal:
        """Transform concat string argument."""
        token = children[0]
        value = str(token)[1:-1]  # Remove quotes
        return Literal(
            source_location=_make_location(token),
            value=value,
            literal_type="STRING",
        )

    def string_func(self, _meta: Any, children: list[Any]) -> StringFunc:
        """Pass through string function."""
        return cast(StringFunc, children[0])

    def arith_atom(self, _meta: Any, children: list[Any]) -> ArithOperand:
        """Pass through arithmetic atom."""
        return cast(ArithOperand, children[0])

    def arith_paren(self, _meta: Any, children: list[Any]) -> ArithOperand:
        """Handle parenthesized expression."""
        return cast(ArithOperand, children[0])

    def arith_factor(self, _meta: Any, children: list[Any]) -> ArithOperand:
        """Pass through arithmetic factor."""
        return cast(ArithOperand, children[0])

    def arith_term(self, meta: Any, children: list[Any]) -> ArithOperand:
        """Build left-associative tree for * and /."""
        if len(children) == 1:
            return cast(ArithOperand, children[0])

        # Build left-associative tree: a * b / c => ((a * b) / c)
        result: ArithOperand = children[0]
        i = 1
        while i < len(children):
            operator = str(children[i])
            right = children[i + 1]
            result = ArithmeticOp(
                source_location=_make_location_from_meta(meta),
                left=result,
                operator=operator,
                right=right,
            )
            i += 2
        return result

    def arith_expr(self, meta: Any, children: list[Any]) -> ArithOperand:
        """Build left-associative tree for + and -."""
        if len(children) == 1:
            return cast(ArithOperand, children[0])

        # Build left-associative tree: a + b - c => ((a + b) - c)
        result: ArithOperand = children[0]
        i = 1
        while i < len(children):
            operator = str(children[i])
            right = children[i + 1]
            result = ArithmeticOp(
                source_location=_make_location_from_meta(meta),
                left=result,
                operator=operator,
                right=right,
            )
            i += 2
        return result

    def expr(self, _meta: Any, children: list[Any]) -> Condition:
        """Transform an expression (pass through or_expr)."""
        return cast(Condition, children[0])

    def or_expr(self, meta: Any, children: list[Any]) -> Condition:
        """Transform OR expression."""
        if len(children) == 1:
            return cast(Condition, children[0])
        return OrExpr(
            source_location=_make_location_from_meta(meta),
            conditions=tuple(children),
        )

    def and_expr(self, meta: Any, children: list[Any]) -> Condition:
        """Transform AND expression."""
        if len(children) == 1:
            return cast(Condition, children[0])
        return AndExpr(
            source_location=_make_location_from_meta(meta),
            conditions=tuple(children),
        )

    def not_expr(self, _meta: Any, children: list[Any]) -> Condition:
        """Pass through not_expr (comparison)."""
        return cast(Condition, children[0])

    def negation(self, meta: Any, children: list[Any]) -> NotExpr:
        """Transform NOT expression."""
        return NotExpr(
            source_location=_make_location_from_meta(meta),
            operand=children[0],
        )

    def grouped_expr(self, _meta: Any, children: list[Any]) -> Condition:
        """Transform grouped expression (parenthesized or_expr)."""
        return cast(Condition, children[0])

    def comparison(self, _meta: Any, children: list[Any]) -> Condition:
        """Pass through comparison."""
        return cast(Condition, children[0])

    def binary_comparison(self, meta: Any, children: list[Any]) -> BinaryOp:
        """Transform a binary comparison (NAME op value)."""
        left, operator, right = children
        return BinaryOp(
            source_location=_make_location_from_meta(meta),
            left=left,
            operator=operator,
            right=right,
        )

    def is_null_check(self, meta: Any, children: list[Any]) -> IsNullCheck:
        """Transform IS_NULL check."""
        return IsNullCheck(
            source_location=_make_location_from_meta(meta),
            operand=children[0],
            negated=False,
        )

    def is_not_null_check(self, meta: Any, children: list[Any]) -> IsNullCheck:
        """Transform IS_NOT_NULL check."""
        return IsNullCheck(
            source_location=_make_location_from_meta(meta),
            operand=children[0],
            negated=True,
        )

    def is_null_check_alias(self, meta: Any, children: list[Any]) -> IsNullCheck:
        """Transform == NULL check (alias for IS_NULL)."""
        return IsNullCheck(
            source_location=_make_location_from_meta(meta),
            operand=children[0],
            negated=False,
        )

    def is_not_null_check_alias(self, meta: Any, children: list[Any]) -> IsNullCheck:
        """Transform != NULL check (alias for IS_NOT_NULL)."""
        return IsNullCheck(
            source_location=_make_location_from_meta(meta),
            operand=children[0],
            negated=True,
        )

    def in_check(self, meta: Any, children: list[Any]) -> InCheck:
        """Transform IN check."""
        operand = children[0]
        values = children[1]  # value_list returns tuple
        return InCheck(
            source_location=_make_location_from_meta(meta),
            operand=operand,
            values=values,
        )

    def between_check(self, meta: Any, children: list[Any]) -> BetweenCheck:
        """Transform BETWEEN check."""
        operand, low, high = children
        return BetweenCheck(
            source_location=_make_location_from_meta(meta),
            operand=operand,
            low=low,
            high=high,
        )

    def value_list(self, _meta: Any, children: list[Any]) -> tuple[Literal, ...]:
        """Transform a list of values."""
        return tuple(children)

    def value(self, _meta: Any, children: list[Any]) -> Literal:
        """Pass through value."""
        return cast(Literal, children[0])

    def filter_op(self, meta: Any, children: list[Any]) -> Filter:
        """Transform a FILTER operation."""
        source, condition, target = children
        return Filter(
            source_location=_make_location_from_meta(meta),
            source=source,
            condition=condition,
            target=target,
        )

    def name_list(self, _meta: Any, children: list[Any]) -> tuple[Identifier, ...]:
        """Transform a list of column names."""
        return tuple(children)

    def select_op(self, meta: Any, children: list[Any]) -> Select:
        """Transform a SELECT operation."""
        columns, source, target = children
        return Select(
            source_location=_make_location_from_meta(meta),
            columns=columns,
            source=source,
            target=target,
        )

    def map_op(self, meta: Any, children: list[Any]) -> Map:
        """Transform a MAP operation."""
        source, new_column, expression, target = children
        return Map(
            source_location=_make_location_from_meta(meta),
            source=source,
            new_column=new_column,
            expression=expression,
            target=target,
        )

    def sort_asc(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform ASC sort order."""
        return False  # descending = False

    def sort_desc(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform DESC sort order."""
        return True  # descending = True

    def sort_order(self, _meta: Any, children: list[Any]) -> bool:
        """Pass through sort order."""
        return cast(bool, children[0])

    def nulls_first(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform NULLS_FIRST."""
        return False  # nulls_last = False

    def nulls_last(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform NULLS_LAST."""
        return True  # nulls_last = True

    def nulls_order(self, _meta: Any, children: list[Any]) -> bool:
        """Pass through nulls order."""
        return cast(bool, children[0])

    def sort_op(self, meta: Any, children: list[Any]) -> Sort:
        """Transform a SORT operation."""
        # Children: source, key, descending, [nulls_order], target
        source = children[0]
        key = children[1]
        descending = children[2]
        # Check if nulls_order is present (optional)
        if len(children) == 5:
            nulls_last: Optional[bool] = children[3]
            target = children[4]
        else:
            nulls_last = None
            target = children[3]
        return Sort(
            source_location=_make_location_from_meta(meta),
            source=source,
            key=key,
            descending=descending,
            nulls_last=nulls_last,
            target=target,
        )

    def limit_op(self, meta: Any, children: list[Any]) -> Limit:
        """Transform a LIMIT operation."""
        source, count_token, target = children
        count = int(str(count_token))
        return Limit(
            source_location=_make_location_from_meta(meta),
            source=source,
            count=count,
            target=target,
        )

    def skip_op(self, meta: Any, children: list[Any]) -> Skip:
        """Transform a SKIP operation."""
        source, count_token, target = children
        count = int(str(count_token))
        return Skip(
            source_location=_make_location_from_meta(meta),
            source=source,
            count=count,
            target=target,
        )

    def distinct_op(self, meta: Any, children: list[Any]) -> Distinct:
        """Transform a DISTINCT operation."""
        source, keys, target = children
        return Distinct(
            source_location=_make_location_from_meta(meta),
            source=source,
            keys=keys,
            target=target,
        )

    def aggregate_op(self, meta: Any, children: list[Any]) -> Aggregate:
        """Transform an AGGREGATE operation."""
        source = children[0]
        group_by: Optional[tuple[Identifier, ...]] = None
        computations: tuple[AggExpr, ...] = ()
        target = children[-1]

        for child in children[1:-1]:
            if isinstance(child, tuple) and child and isinstance(child[0], Identifier):
                # Could be group_by or computations
                if not computations:
                    # First tuple - could be either
                    # Check if it's an AggExpr tuple
                    if child and isinstance(child[0], AggExpr):
                        computations = child
                    else:
                        group_by = child
            elif isinstance(child, tuple) and child and isinstance(child[0], AggExpr):
                computations = child

        return Aggregate(
            source_location=_make_location_from_meta(meta),
            source=source,
            group_by=group_by,
            computations=computations,
            target=target,
        )

    def group_clause(self, _meta: Any, children: list[Any]) -> tuple[Identifier, ...]:
        """Transform GROUP_BY clause."""
        return cast(tuple[Identifier, ...], children[0])  # name_list returns tuple

    def compute_clause(self, _meta: Any, children: list[Any]) -> tuple[AggExpr, ...]:
        """Transform COMPUTE clause."""
        return tuple(children)

    def agg_expr(self, meta: Any, children: list[Any]) -> AggExpr:
        """Transform aggregate expression."""
        func, alias = children
        return AggExpr(
            source_location=_make_location_from_meta(meta),
            func=func,
            alias=alias,
        )

    def count_func(self, meta: Any, children: list[Any]) -> AggFunc:
        """Transform COUNT function."""
        column = children[0] if children else None
        return AggFunc(
            source_location=_make_location_from_meta(meta),
            func_name="COUNT",
            column=column,
        )

    def sum_func(self, meta: Any, children: list[Any]) -> AggFunc:
        """Transform SUM function."""
        return AggFunc(
            source_location=_make_location_from_meta(meta),
            func_name="SUM",
            column=children[0],
        )

    def avg_func(self, meta: Any, children: list[Any]) -> AggFunc:
        """Transform AVG function."""
        return AggFunc(
            source_location=_make_location_from_meta(meta),
            func_name="AVG",
            column=children[0],
        )

    def min_func(self, meta: Any, children: list[Any]) -> AggFunc:
        """Transform MIN function."""
        return AggFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MIN",
            column=children[0],
        )

    def max_func(self, meta: Any, children: list[Any]) -> AggFunc:
        """Transform MAX function."""
        return AggFunc(
            source_location=_make_location_from_meta(meta),
            func_name="MAX",
            column=children[0],
        )

    def agg_func(self, _meta: Any, children: list[Any]) -> AggFunc:
        """Pass through aggregate function."""
        return cast(AggFunc, children[0])

    # =========================================================================
    # File I/O operation transformers
    # =========================================================================

    def json_format(self, _meta: Any, _children: list[Any]) -> str:
        """Transform JSON format type."""
        return "JSON"

    def csv_format(self, _meta: Any, _children: list[Any]) -> str:
        """Transform CSV format type."""
        return "CSV"

    def format_type(self, _meta: Any, children: list[Any]) -> str:
        """Pass through format type."""
        return cast(str, children[0])

    def read_op(self, meta: Any, children: list[Any]) -> Read:
        """Transform a READ operation."""
        path_token, format_type, target = children
        # Remove quotes from path
        path_value = str(path_token)[1:-1]
        path = Literal(
            source_location=_make_location(path_token),
            value=path_value,
            literal_type="STRING",
        )
        return Read(
            source_location=_make_location_from_meta(meta),
            path=path,
            format=format_type,
            target=target,
        )

    def write_op(self, meta: Any, children: list[Any]) -> Write:
        """Transform a WRITE operation."""
        source, path_token, format_type = children
        # Remove quotes from path
        path_value = str(path_token)[1:-1]
        path = Literal(
            source_location=_make_location(path_token),
            value=path_value,
            literal_type="STRING",
        )
        return Write(
            source_location=_make_location_from_meta(meta),
            source=source,
            path=path,
            format=format_type,
        )

    # =========================================================================
    # HTTP operation transformers
    # =========================================================================

    def get_method(self, _meta: Any, _children: list[Any]) -> str:
        """Transform GET method."""
        return "GET"

    def post_method(self, _meta: Any, _children: list[Any]) -> str:
        """Transform POST method."""
        return "POST"

    def put_method(self, _meta: Any, _children: list[Any]) -> str:
        """Transform PUT method."""
        return "PUT"

    def delete_method(self, _meta: Any, _children: list[Any]) -> str:
        """Transform DELETE method."""
        return "DELETE"

    def http_method(self, _meta: Any, children: list[Any]) -> str:
        """Pass through HTTP method."""
        return cast(str, children[0])

    def obj_string(self, _meta: Any, children: list[Any]) -> str:
        """Transform object literal string value."""
        token = children[0]
        return str(token)[1:-1]  # Remove quotes

    def obj_number(self, _meta: Any, children: list[Any]) -> Union[int, float]:
        """Transform object literal number value."""
        token = children[0]
        value_str = str(token)
        return float(value_str) if "." in value_str else int(value_str)

    def obj_true(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform object literal true value."""
        return True

    def obj_false(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform object literal false value."""
        return False

    def obj_null(self, _meta: Any, _children: list[Any]) -> None:
        """Transform object literal null value."""
        return None

    def literal_value(self, _meta: Any, children: list[Any]) -> Any:
        """Pass through literal value."""
        return children[0]

    def key_value(self, _meta: Any, children: list[Any]) -> tuple[str, Any]:
        """Transform a key-value pair."""
        key_token, value = children
        key = str(key_token)[1:-1]  # Remove quotes
        return (key, value)

    def object_literal(self, meta: Any, children: list[Any]) -> ObjectLiteral:
        """Transform an object literal."""
        pairs = tuple(children)
        return ObjectLiteral(
            source_location=_make_location_from_meta(meta),
            pairs=pairs,
        )

    def headers_clause(self, _meta: Any, children: list[Any]) -> ObjectLiteral:
        """Transform headers clause."""
        return cast(ObjectLiteral, children[0])

    def fetch_op(self, meta: Any, children: list[Any]) -> Fetch:
        """Transform a FETCH operation."""
        url_token = children[0]
        method = children[1]
        # Check if headers are present
        if len(children) == 4:
            headers = children[2]
            target = children[3]
        else:
            headers = None
            target = children[2]

        # Create URL literal
        url_value = str(url_token)[1:-1]  # Remove quotes
        url = Literal(
            source_location=_make_location(url_token),
            value=url_value,
            literal_type="STRING",
        )

        return Fetch(
            source_location=_make_location_from_meta(meta),
            url=url,
            method=method,
            headers=headers,
            target=target,
        )

    def post_object_body(self, _meta: Any, children: list[Any]) -> ObjectLiteral:
        """Transform POST body as object literal."""
        return cast(ObjectLiteral, children[0])

    def post_var_body(self, _meta: Any, children: list[Any]) -> Identifier:
        """Transform POST body as variable reference."""
        return cast(Identifier, children[0])

    def post_body(self, _meta: Any, children: list[Any]) -> Union[ObjectLiteral, Identifier]:
        """Pass through post body."""
        return cast(Union[ObjectLiteral, Identifier], children[0])

    def post_op(self, meta: Any, children: list[Any]) -> Post:
        """Transform a POST operation."""
        url_token = children[0]
        body = children[1]
        # Check if headers are present
        if len(children) == 4:
            headers = children[2]
            target = children[3]
        else:
            headers = None
            target = children[2]

        # Create URL literal
        url_value = str(url_token)[1:-1]  # Remove quotes
        url = Literal(
            source_location=_make_location(url_token),
            value=url_value,
            literal_type="STRING",
        )

        return Post(
            source_location=_make_location_from_meta(meta),
            url=url,
            body=body,
            headers=headers,
            target=target,
        )

    # =========================================================================
    # JOIN operation transformers
    # =========================================================================

    def join_condition(self, meta: Any, children: list[Any]) -> JoinCondition:
        """Transform a JOIN condition."""
        left_table = children[0]
        left_field = children[1]
        right_table = children[2]
        right_field = children[3]
        return JoinCondition(
            source_location=_make_location_from_meta(meta),
            left_table=left_table.name,
            left_field=left_field.name,
            right_table=right_table.name,
            right_field=right_field.name,
        )

    def join_op(self, meta: Any, children: list[Any]) -> Join:
        """Transform a JOIN operation."""
        left, right, condition, target = children
        return Join(
            source_location=_make_location_from_meta(meta),
            left=left,
            right=right,
            condition=condition,
            target=target,
        )

    def left_join_op(self, meta: Any, children: list[Any]) -> LeftJoin:
        """Transform a LEFT_JOIN operation."""
        left, right, condition, target = children
        return LeftJoin(
            source_location=_make_location_from_meta(meta),
            left=left,
            right=right,
            condition=condition,
            target=target,
        )

    # =========================================================================
    # RENAME operation transformers
    # =========================================================================

    def rename_clause(self, meta: Any, children: list[Any]) -> RenameClause:
        """Transform a rename clause (WITH old AS new)."""
        old_name, new_name = children
        return RenameClause(
            source_location=_make_location_from_meta(meta),
            old_name=old_name,
            new_name=new_name,
        )

    def rename_op(self, meta: Any, children: list[Any]) -> Rename:
        """Transform a RENAME operation."""
        source = children[0]
        target = children[-1]
        renames = [c for c in children[1:-1] if isinstance(c, RenameClause)]
        return Rename(
            source_location=_make_location_from_meta(meta),
            source=source,
            renames=tuple(renames),
            target=target,
        )

    # =========================================================================
    # DROP operation transformers
    # =========================================================================

    def drop_op(self, meta: Any, children: list[Any]) -> Drop:
        """Transform a DROP operation."""
        source, columns, target = children
        return Drop(
            source_location=_make_location_from_meta(meta),
            source=source,
            columns=columns,
            target=target,
        )

    # =========================================================================
    # UNION operation transformers
    # =========================================================================

    def union_op(self, meta: Any, children: list[Any]) -> UnionOp:
        """Transform a UNION operation."""
        left, right, target = children
        return UnionOp(
            source_location=_make_location_from_meta(meta),
            left=left,
            right=right,
            target=target,
            all=False,
        )

    def union_all_op(self, meta: Any, children: list[Any]) -> UnionOp:
        """Transform a UNION_ALL operation."""
        left, right, target = children
        return UnionOp(
            source_location=_make_location_from_meta(meta),
            left=left,
            right=right,
            target=target,
            all=True,
        )

    # =========================================================================
    # SLICE operation transformers
    # =========================================================================

    def slice_op(self, meta: Any, children: list[Any]) -> Slice:
        """Transform a SLICE operation."""
        source, start_token, end_token, target = children
        start = int(str(start_token))
        end = int(str(end_token))
        return Slice(
            source_location=_make_location_from_meta(meta),
            source=source,
            start=start,
            end=end,
            target=target,
        )

    # =========================================================================
    # ADD_COLUMN operation transformers
    # =========================================================================

    def add_column_op(self, meta: Any, children: list[Any]) -> AddColumn:
        """Transform an ADD_COLUMN operation."""
        source, column_name, default_value, target = children
        return AddColumn(
            source_location=_make_location_from_meta(meta),
            source=source,
            column_name=column_name,
            default_value=default_value,
            target=target,
        )

    # =========================================================================
    # PRINT/LOG statement transformers
    # =========================================================================

    def print_stmt(self, meta: Any, children: list[Any]) -> PrintStatement:
        """Transform PRINT statement."""
        return PrintStatement(
            source_location=_make_location_from_meta(meta),
            value=children[0],
        )

    def log_info(self, meta: Any, children: list[Any]) -> LogStatement:
        """Transform LOG_INFO statement."""
        return LogStatement(
            source_location=_make_location_from_meta(meta),
            level="INFO",
            value=children[0],
        )

    def log_warn(self, meta: Any, children: list[Any]) -> LogStatement:
        """Transform LOG_WARN statement."""
        return LogStatement(
            source_location=_make_location_from_meta(meta),
            level="WARN",
            value=children[0],
        )

    def log_error(self, meta: Any, children: list[Any]) -> LogStatement:
        """Transform LOG_ERROR statement."""
        return LogStatement(
            source_location=_make_location_from_meta(meta),
            level="ERROR",
            value=children[0],
        )

    def log_debug(self, meta: Any, children: list[Any]) -> LogStatement:
        """Transform LOG_DEBUG statement."""
        return LogStatement(
            source_location=_make_location_from_meta(meta),
            level="DEBUG",
            value=children[0],
        )

    def log_stmt(self, _meta: Any, children: list[Any]) -> LogStatement:
        """Pass through log statement."""
        return cast(LogStatement, children[0])

    def body_print(self, _meta: Any, children: list[Any]) -> PrintStatement:
        """Transform pipeline body PRINT statement."""
        return cast(PrintStatement, children[0])

    def body_log(self, _meta: Any, children: list[Any]) -> LogStatement:
        """Transform pipeline body LOG statement."""
        return cast(LogStatement, children[0])

    def operation(
        self, _meta: Any, children: list[Any]
    ) -> Union[Filter, Select, Map, Sort, Limit, Skip, Distinct, Aggregate, Read, Write, Fetch, Post, Join, LeftJoin, Rename, Drop, UnionOp, Slice, AddColumn]:
        """Pass through operation."""
        return cast(
            Union[Filter, Select, Map, Sort, Limit, Skip, Distinct, Aggregate, Read, Write, Fetch, Post, Join, LeftJoin, Rename, Drop, UnionOp, Slice, AddColumn],
            children[0]
        )

    def step(self, meta: Any, children: list[Any]) -> Step:
        """Transform a STEP declaration."""
        name, operation = children
        return Step(
            source_location=_make_location_from_meta(meta),
            name=name,
            operation=operation,
        )

    # Type transformers
    def int_type(self, meta: Any, _children: list[Any]) -> TypeName:
        """Transform INT type."""
        return TypeName(
            source_location=_make_location_from_meta(meta),
            name="INT",
        )

    def string_type(self, meta: Any, _children: list[Any]) -> TypeName:
        """Transform STRING type."""
        return TypeName(
            source_location=_make_location_from_meta(meta),
            name="STRING",
        )

    def decimal_type(self, meta: Any, _children: list[Any]) -> TypeName:
        """Transform DECIMAL type."""
        return TypeName(
            source_location=_make_location_from_meta(meta),
            name="DECIMAL",
        )

    def bool_type(self, meta: Any, _children: list[Any]) -> TypeName:
        """Transform BOOL type."""
        return TypeName(
            source_location=_make_location_from_meta(meta),
            name="BOOL",
        )

    def date_type(self, meta: Any, _children: list[Any]) -> TypeName:
        """Transform DATE type."""
        return TypeName(
            source_location=_make_location_from_meta(meta),
            name="DATE",
        )

    def datetime_type(self, meta: Any, _children: list[Any]) -> TypeName:
        """Transform DATETIME type."""
        return TypeName(
            source_location=_make_location_from_meta(meta),
            name="DATETIME",
        )

    def field(self, meta: Any, children: list[Any]) -> FieldDef:
        """Transform a field definition."""
        name, type_name = children
        return FieldDef(
            source_location=_make_location_from_meta(meta),
            name=name,
            type_name=type_name,
        )

    def field_list(self, _meta: Any, children: list[Any]) -> tuple[FieldDef, ...]:
        """Transform a list of fields."""
        return tuple(children)

    def table_type(self, meta: Any, children: list[Any]) -> TableType:
        """Transform a TABLE type."""
        fields = children[0] if children else ()
        return TableType(
            source_location=_make_location_from_meta(meta),
            fields=fields,
        )

    def type_expr(self, _meta: Any, children: list[Any]) -> TableType:
        """Transform a type expression."""
        return cast(TableType, children[0])

    def input_decl(self, meta: Any, children: list[Any]) -> Input:
        """Transform an INPUT declaration."""
        name, type_expr = children
        return Input(
            source_location=_make_location_from_meta(meta),
            name=name,
            type_expr=type_expr,
        )

    def output_decl(self, meta: Any, children: list[Any]) -> Output:
        """Transform an OUTPUT declaration."""
        name = children[0]
        return Output(
            source_location=_make_location_from_meta(meta),
            name=name,
        )

    # =========================================================================
    # Control Flow statement transformers
    # =========================================================================

    def set_arith_value(self, _meta: Any, children: list[Any]) -> Any:
        """Transform SET arithmetic value."""
        return children[0]

    def set_true_value(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform SET true value."""
        return True

    def set_false_value(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform SET false value."""
        return False

    def set_value(self, _meta: Any, children: list[Any]) -> Any:
        """Pass through set value."""
        return children[0]

    def set_stmt(self, meta: Any, children: list[Any]) -> SetStatement:
        """Transform a SET statement."""
        variable, value = children
        return SetStatement(
            source_location=_make_location_from_meta(meta),
            variable=variable,
            value=value,
        )

    def body_step(self, _meta: Any, children: list[Any]) -> Step:
        """Transform pipeline body step."""
        return cast(Step, children[0])

    def body_set(self, _meta: Any, children: list[Any]) -> SetStatement:
        """Transform pipeline body SET statement."""
        return cast(SetStatement, children[0])

    def body_if(self, _meta: Any, children: list[Any]) -> IfStatement:
        """Transform pipeline body IF statement."""
        return cast(IfStatement, children[0])

    def pipeline_body(
        self, _meta: Any, children: list[Any]
    ) -> Union[Step, SetStatement, IfStatement]:
        """Pass through pipeline body item."""
        return cast(Union[Step, SetStatement, IfStatement], children[0])

    # IF/ELSE statement transformers
    def if_condition(self, _meta: Any, children: list[Any]) -> Condition:
        """Transform IF condition."""
        return cast(Condition, children[0])

    def if_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Union[Step, SetStatement, IfStatement], ...]:
        """Transform IF body."""
        return tuple(children)

    def else_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Union[Step, SetStatement, IfStatement], ...]:
        """Transform ELSE body."""
        return cast(
            tuple[Union[Step, SetStatement, IfStatement], ...],
            children[0]
        )  # if_body already returns a tuple

    def else_if(self, _meta: Any, children: list[Any]) -> IfStatement:
        """Transform ELSE IF (chained)."""
        # Return the nested if_stmt as-is
        return cast(IfStatement, children[0])

    def if_stmt(self, meta: Any, children: list[Any]) -> IfStatement:
        """Transform IF statement."""
        condition = children[0]
        then_body = children[1]
        else_body = None

        if len(children) > 2:
            else_clause = children[2]
            # ELSE IF case - wrap in tuple; ELSE case - already a tuple
            else_body = (else_clause,) if isinstance(else_clause, IfStatement) else else_clause

        return IfStatement(
            source_location=_make_location_from_meta(meta),
            condition=condition,
            then_body=then_body,
            else_body=else_body,
        )

    # FOR_EACH statement transformers
    def body_for_each(self, _meta: Any, children: list[Any]) -> ForEachStatement:
        """Transform pipeline body FOR_EACH statement."""
        return cast(ForEachStatement, children[0])

    def for_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Union[Step, SetStatement, IfStatement, ForEachStatement], ...]:
        """Transform FOR_EACH body."""
        return tuple(children)

    def for_each_stmt(self, meta: Any, children: list[Any]) -> ForEachStatement:
        """Transform FOR_EACH statement."""
        item_var, collection, body = children
        return ForEachStatement(
            source_location=_make_location_from_meta(meta),
            item_var=item_var,
            collection=collection,
            body=body,
        )

    # WHILE statement transformers
    def body_while(self, _meta: Any, children: list[Any]) -> WhileStatement:
        """Transform pipeline body WHILE statement."""
        return cast(WhileStatement, children[0])

    def while_condition(self, _meta: Any, children: list[Any]) -> Condition:
        """Transform WHILE condition."""
        return cast(Condition, children[0])

    def while_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Union[Step, SetStatement, IfStatement, ForEachStatement, WhileStatement], ...]:
        """Transform WHILE body."""
        return tuple(children)

    def while_stmt(self, meta: Any, children: list[Any]) -> WhileStatement:
        """Transform WHILE statement."""
        condition, body = children
        return WhileStatement(
            source_location=_make_location_from_meta(meta),
            condition=condition,
            body=body,
        )

    # TRY/ON_ERROR statement transformers
    def body_try(self, _meta: Any, children: list[Any]) -> TryStatement:
        """Transform pipeline body TRY statement."""
        return cast(TryStatement, children[0])

    def try_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Union[Step, SetStatement, IfStatement, ForEachStatement, WhileStatement, TryStatement], ...]:
        """Transform TRY body."""
        return tuple(children)

    def error_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Union[Step, SetStatement, IfStatement, ForEachStatement, WhileStatement, TryStatement], ...]:
        """Transform ON_ERROR body."""
        return tuple(children)

    def try_stmt(self, meta: Any, children: list[Any]) -> TryStatement:
        """Transform TRY/ON_ERROR statement."""
        try_body, error_body = children
        return TryStatement(
            source_location=_make_location_from_meta(meta),
            try_body=try_body,
            error_body=error_body,
        )

    # MATCH statement transformers
    def body_match(self, _meta: Any, children: list[Any]) -> MatchStatement:
        """Transform pipeline body MATCH statement."""
        return cast(MatchStatement, children[0])

    def match_number(self, _meta: Any, children: list[Any]) -> Union[int, float]:
        """Transform MATCH case number value."""
        token = children[0]
        value_str = str(token)
        return float(value_str) if "." in value_str else int(value_str)

    def match_string(self, _meta: Any, children: list[Any]) -> str:
        """Transform MATCH case string value."""
        token = children[0]
        return str(token)[1:-1]  # Remove quotes

    def match_true(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform MATCH case true value."""
        return True

    def match_false(self, _meta: Any, _children: list[Any]) -> bool:
        """Transform MATCH case false value."""
        return False

    def match_value(self, _meta: Any, children: list[Any]) -> Union[int, float, str, bool]:
        """Pass through match value."""
        return cast(Union[int, float, str, bool], children[0])

    def match_body(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Any, ...]:
        """Transform MATCH case body."""
        return tuple(children)

    def match_case(self, meta: Any, children: list[Any]) -> MatchCase:
        """Transform a single CASE in MATCH."""
        value, body = children
        return MatchCase(
            source_location=_make_location_from_meta(meta),
            value=value,
            body=body,
        )

    def default_case(
        self, _meta: Any, children: list[Any]
    ) -> tuple[Any, ...]:
        """Transform DEFAULT case body."""
        return cast(tuple[Any, ...], children[0])  # match_body already returns tuple

    def match_stmt(self, meta: Any, children: list[Any]) -> MatchStatement:
        """Transform MATCH statement."""
        variable = children[0]
        cases: list[MatchCase] = []
        default_body = None

        for child in children[1:]:
            if isinstance(child, MatchCase):
                cases.append(child)
            elif isinstance(child, tuple):
                # default_case returns a tuple
                default_body = child

        return MatchStatement(
            source_location=_make_location_from_meta(meta),
            variable=variable,
            cases=tuple(cases),
            default_body=default_body,
        )

    # ASSERT statement transformers
    def body_assert(self, _meta: Any, children: list[Any]) -> AssertStatement:
        """Transform pipeline body ASSERT statement."""
        return cast(AssertStatement, children[0])

    def assert_message(self, _meta: Any, children: list[Any]) -> str:
        """Transform ASSERT message."""
        token = children[0]
        return str(token)[1:-1]  # Remove quotes

    def assert_stmt(self, meta: Any, children: list[Any]) -> AssertStatement:
        """Transform ASSERT statement."""
        condition = children[0]
        message = children[1] if len(children) > 1 else None
        return AssertStatement(
            source_location=_make_location_from_meta(meta),
            condition=condition,
            message=message,
        )

    # RETURN statement transformers
    def body_return(self, _meta: Any, children: list[Any]) -> ReturnStatement:
        """Transform pipeline body RETURN statement."""
        return cast(ReturnStatement, children[0])

    def return_stmt(self, meta: Any, children: list[Any]) -> ReturnStatement:
        """Transform RETURN statement."""
        value = children[0] if children else None
        return ReturnStatement(
            source_location=_make_location_from_meta(meta),
            value=value,
        )

    # BREAK statement transformers
    def body_break(self, _meta: Any, children: list[Any]) -> BreakStatement:
        """Transform pipeline body BREAK statement."""
        return cast(BreakStatement, children[0])

    def break_stmt(self, meta: Any, _children: list[Any]) -> BreakStatement:
        """Transform BREAK statement."""
        return BreakStatement(
            source_location=_make_location_from_meta(meta),
        )

    # CONTINUE statement transformers
    def body_continue(self, _meta: Any, children: list[Any]) -> ContinueStatement:
        """Transform pipeline body CONTINUE statement."""
        return cast(ContinueStatement, children[0])

    def continue_stmt(self, meta: Any, _children: list[Any]) -> ContinueStatement:
        """Transform CONTINUE statement."""
        return ContinueStatement(
            source_location=_make_location_from_meta(meta),
        )

    # APPEND statement transformers
    def body_append(self, _meta: Any, children: list[Any]) -> AppendStatement:
        """Transform pipeline body APPEND statement."""
        return cast(AppendStatement, children[0])

    def append_stmt(self, meta: Any, children: list[Any]) -> AppendStatement:
        """Transform APPEND statement."""
        source, target = children
        return AppendStatement(
            source_location=_make_location_from_meta(meta),
            source=source,
            target=target,
        )

    def pipeline(self, meta: Any, children: list[Any]) -> Pipeline:
        """Transform a PIPELINE declaration."""
        name = children[0]
        inputs: list[Input] = []
        steps: list[Step] = []
        body: list[Any] = []
        output: Optional[Output] = None

        for child in children[1:]:
            if isinstance(child, Input):
                inputs.append(child)
            elif isinstance(child, Step):
                steps.append(child)
                body.append(child)
            elif isinstance(child, (
                SetStatement, IfStatement, ForEachStatement, WhileStatement,
                TryStatement, MatchStatement, AssertStatement, ReturnStatement,
                BreakStatement, ContinueStatement, AppendStatement,
                PrintStatement, LogStatement
            )):
                body.append(child)
            elif isinstance(child, Output):
                output = child

        return Pipeline(
            source_location=_make_location_from_meta(meta),
            name=name,
            inputs=tuple(inputs),
            steps=tuple(steps),
            body=tuple(body),
            outputs=output,
        )

    def start(self, _meta: Any, children: list[Any]) -> Pipeline:
        """Transform the start rule."""
        return cast(Pipeline, children[0])


class Parser:
    """Anka source code parser.

    Parses Anka source code into an AST.
    """

    def __init__(self) -> None:
        """Initialize the parser with the Anka grammar."""
        grammar_text = GRAMMAR_PATH.read_text()
        self._parser = Lark(
            grammar_text,
            start="start",
            parser="lalr",
            propagate_positions=True,
        )
        self._transformer = AnkaTransformer()

    def parse(self, source: str) -> Pipeline:
        """Parse Anka source code into an AST.

        Args:
            source: The Anka source code to parse.

        Returns:
            The parsed Pipeline AST node.

        Raises:
            lark.exceptions.LarkError: If parsing fails.
        """
        tree = self._parser.parse(source)
        return self._transformer.transform(tree)

    def parse_file(self, path: Union[str, Path]) -> Pipeline:
        """Parse an Anka source file into an AST.

        Args:
            path: Path to the .anka file.

        Returns:
            The parsed Pipeline AST node.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            lark.exceptions.LarkError: If parsing fails.
        """
        source = Path(path).read_text()
        return self.parse(source)
