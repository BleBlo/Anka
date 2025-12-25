# Anka Syntax Guide

Anka is a domain-specific language for data transformations, designed for LLM code generation accuracy.

## Design Principles

1. **One way to do things** — No alternative syntax for the same operation
2. **Verbose keywords** — `FILTER` instead of symbols like `?`
3. **Explicit types** — All data boundaries have type annotations
4. **Flat pipelines** — No deep nesting of operations
5. **Named parameters** — No positional argument confusion
6. **Mandatory step names** — Forces logical decomposition
7. **No significant whitespace** — Indentation is for readability only

## Basic Structure

Every Anka program is a `PIPELINE`:

```
PIPELINE pipeline_name:
  INPUT input_name: TYPE

  STEP step_name:
    OPERATION

  OUTPUT output_name
```

## Types

### Primitive Types

- `INT` — Integer numbers
- `DECIMAL` — Decimal numbers (for financial data)
- `STRING` — Text
- `BOOL` — True/False

### Composite Types

- `TABLE[field: TYPE, ...]` — Tabular data with named, typed columns

Example:
```
TABLE[order_id: INT, customer: STRING, amount: DECIMAL]
```

## Operations

### FILTER

Filter rows based on a condition:

```
STEP filter_large:
  FILTER source_table
  WHERE column > value
  INTO target_table
```

Comparison operators: `>`, `<`, `>=`, `<=`, `==`, `!=`

### SELECT

Select specific columns:

```
STEP select_columns:
  SELECT column1, column2
  FROM source_table
  INTO target_table
```

### MAP

Add computed columns:

```
STEP calculate:
  MAP source_table
  WITH new_column => expression
  INTO target_table
```

Example:
```
STEP calc_total:
  MAP orders
  WITH total => amount * quantity
  INTO orders_with_total
```

### SORT

Sort rows by a column:

```
STEP sort_by_amount:
  SORT source_table
  BY column ASC
  INTO sorted_table
```

Options: `ASC` (ascending), `DESC` (descending), `NULLS_FIRST`, `NULLS_LAST`

### LIMIT

Take the first N rows:

```
STEP take_top:
  LIMIT source_table
  COUNT 10
  INTO limited
```

### SKIP

Skip the first N rows:

```
STEP skip_header:
  SKIP source_table
  COUNT 5
  INTO rest
```

### DISTINCT

Remove duplicate rows:

```
STEP unique:
  DISTINCT source_table
  BY column1, column2
  INTO unique_rows
```

### AGGREGATE

Group and compute aggregates:

```
STEP summarize:
  AGGREGATE source_table
  GROUP_BY category
  COMPUTE SUM(amount) AS total, COUNT() AS count
  INTO summary
```

Aggregate functions: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`

## File I/O Operations

### READ

Load data from a file:

```
STEP load_data:
  READ "data/users.json"
  FORMAT JSON
  INTO users
```

Supported formats: `JSON`, `CSV`

Environment variables can be used in paths:
```
STEP load:
  READ "${DATA_DIR}/config.json"
  FORMAT JSON
  INTO config
```

### WRITE

Save data to a file:

```
STEP save_results:
  WRITE results
  TO "output/report.json"
  FORMAT JSON
```

Creates parent directories automatically.

## HTTP Operations

### FETCH

Make HTTP requests:

```
STEP get_users:
  FETCH "https://api.example.com/users"
  METHOD GET
  INTO api_response
```

With headers:
```
STEP get_secure:
  FETCH "https://api.example.com/data"
  METHOD GET
  HEADERS {"Authorization": "Bearer ${API_KEY}"}
  INTO secure_data
```

HTTP methods: `GET`, `POST`, `PUT`, `DELETE`

### POST

Send data via HTTP POST:

```
STEP create_user:
  POST "https://api.example.com/users"
  BODY {"name": "Alice", "email": "alice@example.com"}
  INTO response
```

With variable as body:
```
STEP send_data:
  POST "https://api.example.com/batch"
  BODY processed_data
  INTO response
```

## String Functions

Use string functions in MAP expressions to transform text:

### Basic String Functions

```
STEP transform:
  MAP data
  WITH clean_name => UPPER(TRIM(name))
  INTO result
```

Available functions:
- `UPPER(expr)` — Convert to uppercase
- `LOWER(expr)` — Convert to lowercase
- `TRIM(expr)` — Remove leading/trailing whitespace
- `LTRIM(expr)` — Remove leading whitespace
- `RTRIM(expr)` — Remove trailing whitespace
- `LENGTH(expr)` — Get string length
- `REVERSE(expr)` — Reverse the string

### Substring Functions

- `SUBSTRING(str, start, length)` — Extract substring
- `LEFT(str, count)` — Get first N characters
- `RIGHT(str, count)` — Get last N characters
- `INDEX_OF(str, search)` — Find position of substring (-1 if not found)

### String Manipulation

- `REPLACE(str, old, new)` — Replace first occurrence
- `REPLACE_ALL(str, old, new)` — Replace all occurrences
- `PAD_LEFT(str, length, char)` — Pad on left to length
- `PAD_RIGHT(str, length, char)` — Pad on right to length
- `REPEAT(str, count)` — Repeat string N times
- `CONCAT(str1, str2, ...)` — Concatenate strings

### String Checks in WHERE Clause

Filter using string patterns:

```
STEP filter_emails:
  FILTER users
  WHERE ENDS_WITH(email, ".com")
  INTO com_users
```

Available checks:
- `CONTAINS(field, "pattern")` — Field contains pattern
- `STARTS_WITH(field, "prefix")` — Field starts with prefix
- `ENDS_WITH(field, "suffix")` — Field ends with suffix
- `MATCHES(field, "regex")` — Field matches regular expression

## Date/Time Functions

Use date functions in MAP expressions to work with dates:

### Date Extraction

```
STEP extract_year:
  MAP orders
  WITH year => YEAR(order_date)
  INTO result
```

Available extraction functions:
- `YEAR(date)` — Get year
- `MONTH(date)` — Get month (1-12)
- `DAY(date)` — Get day of month (1-31)
- `HOUR(date)` — Get hour (0-23)
- `MINUTE(date)` — Get minute (0-59)
- `SECOND(date)` — Get second (0-59)
- `DAY_OF_WEEK(date)` — Get day of week (1=Monday, 7=Sunday)
- `WEEK_OF_YEAR(date)` — Get ISO week number (1-53)

### Date Arithmetic

- `ADD_DAYS(date, n)` — Add N days
- `ADD_MONTHS(date, n)` — Add N months
- `ADD_YEARS(date, n)` — Add N years
- `ADD_HOURS(date, n)` — Add N hours
- `DIFF_DAYS(date1, date2)` — Days between dates

### Date Parsing and Formatting

```
STEP parse:
  MAP data
  WITH parsed => PARSE_DATE(date_str, "YYYY-MM-DD")
  INTO result

STEP format:
  MAP data
  WITH formatted => FORMAT_DATE(order_date, "DD/MM/YYYY")
  INTO result
```

Format patterns: `YYYY` (year), `MM` (month), `DD` (day), `HH` (hour), `mm` (minute), `ss` (second)

### Date/Time Generators

- `NOW()` — Current date and time
- `TODAY()` — Current date

### Date Checks in WHERE Clause

Filter using date comparisons:

```
STEP filter_weekend:
  FILTER orders
  WHERE IS_WEEKEND(order_date)
  INTO weekend_orders
```

Available checks:
- `IS_BEFORE(field, date_expr)` — Field is before date
- `IS_AFTER(field, date_expr)` — Field is after date
- `IS_WEEKEND(field)` — Field falls on Saturday or Sunday

## Complete Example

```
PIPELINE transform_orders:
  INPUT orders: TABLE[order_id: INT, customer: STRING, amount: DECIMAL]

  STEP filter_large:
    FILTER orders
    WHERE amount > 1000
    INTO large_orders

  STEP summarize:
    SELECT customer, amount
    FROM large_orders
    INTO summary

  OUTPUT summary
```

## Minimal Example

The simplest valid Anka program:

```
PIPELINE hello:
  INPUT data: TABLE[x: INT]
  OUTPUT data
```

This pipeline accepts a table with one integer column and outputs it unchanged.
