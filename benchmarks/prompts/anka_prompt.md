You are writing code in Anka, a domain-specific language for data transformations.

## Anka Syntax Reference

### Pipeline Structure
Every Anka program is a PIPELINE with INPUTs, STEPs, and an OUTPUT:

```
PIPELINE pipeline_name:
    INPUT table_name: TABLE[col1: TYPE, col2: TYPE, ...]

    STEP step_name:
        OPERATION ...
        INTO result_name

    OUTPUT result_name
```

### Comments
Use `--` for single-line comments:
```
-- This is a comment
PIPELINE example:
    INPUT data: TABLE[id: INT]  -- inline comment
    OUTPUT data
```

### Types
- `INT` - integers (including negative: -5)
- `STRING` - text
- `DECIMAL` - floating-point numbers (including negative: -3.14)
- `BOOL` - true/false (case insensitive: TRUE, True, true)

### Data Operations

#### FILTER - Keep rows matching a condition
```
STEP filter_step:
    FILTER source_table
    WHERE column > 100
    INTO filtered_result
```
Comparison operators: `>`, `<`, `>=`, `<=`, `==`, `!=`

**Null checks:**
```
FILTER data WHERE amount IS_NULL INTO null_rows
FILTER data WHERE amount IS_NOT_NULL INTO non_null_rows
```

**IN clause:**
```
FILTER data WHERE status IN ("active", "pending") INTO filtered
```

**BETWEEN clause:**
```
FILTER data WHERE value BETWEEN 10 AND 100 INTO in_range
```

**Logical operators (AND, OR, NOT):**
```
FILTER data WHERE amount > 100 AND status == "active" INTO result
FILTER data WHERE category == "A" OR category == "B" INTO result
FILTER data WHERE NOT is_deleted INTO active
```

#### SELECT - Choose specific columns
```
STEP select_step:
    SELECT col1, col2
    FROM source_table
    INTO selected_result
```

#### MAP - Add ONE new computed column
**IMPORTANT: Each MAP operation adds exactly ONE column. For multiple columns, use multiple MAP steps in sequence.**

```
STEP map_step:
    MAP source_table
    WITH new_column => expression
    INTO mapped_result
```
Arithmetic operators: `+`, `-`, `*`, `/`
Parentheses for grouping: `(a + b) * c`

**Multiple columns example (use separate MAP steps):**
```
STEP add_total:
    MAP data
    WITH total => quantity * price
    INTO step1

STEP add_discount:
    MAP step1
    WITH discount => total * 0.1
    INTO step2
```

**Handling nulls with COALESCE:**
```
MAP data WITH total => price * COALESCE(quantity, 0) INTO with_total
```

**Inline conditionals with IF:**
```
MAP data WITH category => IF(value > 100, "high", "low") INTO categorized
```

**NULLIF - Returns null if values are equal:**
```
MAP data WITH safe_divisor => NULLIF(divisor, 0) INTO with_safe
```

#### SORT - Order rows by a column
```
SORT source_table BY column DESC INTO sorted_result
```
Use `ASC` for ascending, `DESC` for descending.

**Sorting with null values:**
```
SORT data BY price ASC NULLS_LAST INTO sorted
SORT data BY price ASC NULLS_FIRST INTO sorted
```

#### LIMIT - Take first N rows
```
LIMIT source_table COUNT 5 INTO limited_result
```

#### SKIP - Skip first N rows
```
SKIP source_table COUNT 5 INTO skipped_result
```

#### DISTINCT - Remove duplicate rows
```
DISTINCT orders BY customer_id INTO unique_orders
```

#### AGGREGATE - Group and compute aggregates
```
AGGREGATE orders GROUP_BY category COMPUTE SUM(amount) AS total, COUNT() AS count INTO summary
```
Aggregate functions: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`

### Join Operations

#### JOIN - Inner join two tables
```
JOIN orders WITH customers ON orders.customer_id == customers.id INTO joined
```

#### LEFT_JOIN - Left outer join
```
LEFT_JOIN orders WITH customers ON orders.customer_id == customers.id INTO joined
```

### Column Operations

#### RENAME - Rename columns
```
RENAME data WITH old_name AS new_name INTO renamed
RENAME data WITH a AS x WITH b AS y INTO renamed  -- multiple renames
```

#### DROP - Remove columns
```
DROP data COLUMNS col1, col2 INTO cleaned
```

#### ADD_COLUMN - Add column with default value
```
ADD_COLUMN data COLUMN status DEFAULT "active" INTO with_status
```

### Set Operations

#### UNION - Combine tables (removes duplicates)
```
UNION table1 WITH table2 INTO combined
```

#### UNION_ALL - Combine tables (keeps duplicates)
```
UNION_ALL table1 WITH table2 INTO combined
```

#### SLICE - Pagination/range
```
SLICE data FROM 10 TO 20 INTO page
```

### Control Flow

#### SET - Variable assignment
```
SET counter = 0
SET is_active = TRUE
SET is_deleted = FALSE
SET name = "test"
```

#### IF/ELSE - Conditional execution
```
IF count > 0:
    SET result = 1
ELSE:
    SET result = 0
END
```

#### FOR_EACH - Loop over collection
```
FOR_EACH item IN data:
    SET total = total + 1
END
```

#### WHILE - Conditional loop
```
WHILE counter < 10:
    SET counter = counter + 1
END
```

#### BREAK and CONTINUE
```
WHILE counter < 100:
    SET counter = counter + 1
    IF counter == 50:
        BREAK
    END
END
```

#### TRY/ON_ERROR - Error handling
```
TRY:
    -- risky operation
ON_ERROR:
    SET error_occurred = TRUE
END
```

#### MATCH - Pattern matching
```
MATCH status:
    CASE "active":
        SET priority = 1
    CASE "pending":
        SET priority = 2
    DEFAULT:
        SET priority = 0
END
```

#### ASSERT - Validation
```
ASSERT count > 0 MESSAGE "count must be positive"
```

#### RETURN - Early exit
```
RETURN result
```

#### APPEND - Add to collection
```
APPEND item TO collection
```

#### PRINT and LOG
```
PRINT "Debug message"
PRINT variable
LOG_INFO "Info message"
LOG_WARN "Warning message"
LOG_ERROR "Error message"
LOG_DEBUG "Debug message"
```

### File I/O Operations

#### READ - Load data from file
```
READ "data/users.json" FORMAT JSON INTO users
READ "data/report.csv" FORMAT CSV INTO report
```

#### WRITE - Save data to file
```
WRITE results TO "output/report.json" FORMAT JSON
```

### HTTP Operations

#### FETCH - HTTP GET request
```
FETCH "https://api.example.com/users" METHOD GET INTO api_response

-- With headers:
FETCH "https://api.example.com/data" METHOD GET HEADERS {"Authorization": "Bearer ${API_KEY}"} INTO secure_data
```

#### POST - Send data via HTTP
```
POST "https://api.example.com/users" BODY {"name": "Alice", "email": "alice@example.com"} INTO response
```

### Math Functions
- `ABS(expr)` - Absolute value
- `ROUND(expr, decimals)` - Round to N decimal places
- `FLOOR(expr)` - Round down
- `CEIL(expr)` - Round up
- `MOD(a, b)` - Modulo (remainder)
- `POWER(base, exp)` - Exponentiation
- `SQRT(expr)` - Square root
- `SIGN(expr)` - Returns -1, 0, or 1
- `TRUNC(expr)` - Truncate to integer
- `MIN_VAL(a, b)` - Minimum of two values
- `MAX_VAL(a, b)` - Maximum of two values

Example:
```
MAP data WITH rounded => ROUND(value, 2) INTO result
MAP data WITH absolute => ABS(value) INTO result
```

### Type Casting Functions
- `TO_INT(expr)` - Convert to integer
- `TO_STRING(expr)` - Convert to string
- `TO_DECIMAL(expr)` - Convert to decimal
- `TO_BOOL(expr)` - Convert to boolean

Example:
```
MAP data WITH num => TO_INT(text_value) INTO result
```

### Type Checking Functions (for WHERE clauses)
- `IS_INT(expr)` - Is integer
- `IS_STRING(expr)` - Is string
- `IS_DECIMAL(expr)` - Is decimal
- `IS_BOOL(expr)` - Is boolean
- `IS_LIST(expr)` - Is list
- `IS_DATE(expr)` - Is date
- `IS_EMPTY(expr)` - Is empty (string or list)
- `IS_NUMERIC(expr)` - Is numeric

Example:
```
FILTER data WHERE IS_INT(value) INTO integers_only
FILTER data WHERE IS_EMPTY(name) INTO empty_names
```

### String Functions

**In MAP expressions:**
- `UPPER(expr)`, `LOWER(expr)` - Case conversion
- `TRIM(expr)`, `LTRIM(expr)`, `RTRIM(expr)` - Whitespace removal
- `LENGTH(expr)` - String length
- `REVERSE(expr)` - Reverse string
- `SUBSTRING(str, start, length)` - Extract substring (0-indexed)
- `LEFT(str, n)`, `RIGHT(str, n)` - First/last N characters
- `INDEX_OF(str, substr)` - Find position of substring
- `REPLACE(str, old, new)` - Replace first occurrence
- `REPLACE_ALL(str, old, new)` - Replace all occurrences
- `PAD_LEFT(str, width, char)`, `PAD_RIGHT(str, width, char)` - Pad string
- `REPEAT(str, n)` - Repeat string N times
- `CONCAT(str1, str2, ...)` - Concatenate strings

Example:
```
MAP data WITH clean_name => UPPER(TRIM(name)) INTO result
MAP data WITH full_name => CONCAT(first_name, " ", last_name) INTO result
MAP data WITH padded_id => PAD_LEFT(id, 5, "0") INTO result
```

**In WHERE clauses:**
- `CONTAINS(field, "pattern")` - Field contains pattern
- `STARTS_WITH(field, "prefix")` - Field starts with prefix
- `ENDS_WITH(field, "suffix")` - Field ends with suffix
- `MATCHES(field, "regex")` - Field matches regex

Example:
```
FILTER users WHERE ENDS_WITH(email, ".com") INTO result
FILTER products WHERE CONTAINS(name, "premium") INTO premium
```

### List Functions
- `FIRST(list)` - First element
- `LAST(list)` - Last element
- `NTH(list, index)` - Element at index (0-indexed)
- `FLATTEN(list)` - Flatten nested lists
- `UNIQUE(list)` - Remove duplicates
- `LIST_CONTAINS(list, value)` - Check if list contains value
- `RANGE(start, end)` - Generate list of numbers
- `RANGE(start, end, step)` - Generate with step

Example:
```
MAP data WITH first_item => FIRST(items) INTO result
MAP data WITH nums => RANGE(0, 10) INTO with_range
```

### Date/Time Functions

**Current date/time:**
- `NOW()` - Current datetime
- `TODAY()` - Current date

**Extraction:**
- `YEAR(date)`, `MONTH(date)`, `DAY(date)` - Date components
- `HOUR(date)`, `MINUTE(date)`, `SECOND(date)` - Time components
- `DAY_OF_WEEK(date)` - 1=Monday, 7=Sunday
- `WEEK_OF_YEAR(date)` - ISO week number

**Arithmetic:**
- `ADD_DAYS(date, n)`, `ADD_MONTHS(date, n)`, `ADD_YEARS(date, n)`
- `ADD_HOURS(date, n)`
- `DIFF_DAYS(date1, date2)` - Days between dates

**Parsing/Formatting:**
- `PARSE_DATE(str, "YYYY-MM-DD")` - Parse string to date
- `FORMAT_DATE(date, "DD/MM/YYYY")` - Format date to string

**In WHERE clauses:**
- `IS_BEFORE(field, date_expr)` - Field is before date
- `IS_AFTER(field, date_expr)` - Field is after date
- `IS_WEEKEND(field)` - Field is Saturday or Sunday

Example:
```
MAP orders WITH due_date => ADD_DAYS(order_date, 30) INTO result
FILTER orders WHERE IS_AFTER(order_date, TODAY()) INTO future_orders
```

## Complete Example

```
-- Sales report pipeline with multiple computed columns
PIPELINE sales_report:
    INPUT sales: TABLE[product: STRING, quantity: INT, price: DECIMAL, status: STRING]

    -- Filter active sales with positive quantities
    STEP filter_valid:
        FILTER sales
        WHERE quantity > 0 AND status == "active"
        INTO valid_sales

    -- Calculate total (first computed column)
    STEP calculate_total:
        MAP valid_sales
        WITH total => quantity * COALESCE(price, 0)
        INTO with_totals

    -- Add profit margin (second computed column - uses previous result)
    STEP calculate_margin:
        MAP with_totals
        WITH margin => total * 0.15
        INTO with_margin

    -- Add category based on value (third computed column)
    STEP categorize:
        MAP with_margin
        WITH category => IF(total > 1000, "high", "standard")
        INTO categorized

    -- Sort by total descending
    STEP order_by_value:
        SORT categorized
        BY total DESC
        INTO sorted_sales

    -- Take top 10
    STEP take_top:
        LIMIT sorted_sales
        COUNT 10
        INTO top_sales

    -- Select final columns
    STEP final_columns:
        SELECT product, total, margin, category
        FROM top_sales
        INTO result

    OUTPUT result
```

## Task
{description}

## Input Schema
{input_schema}

Write ONLY the Anka pipeline code. No explanation.
