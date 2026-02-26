# Change Log

All notable changes to the "anka-language" extension will be documented in this file.

## [0.1.0] - 2024-12-24

### Added

- Initial release
- Syntax highlighting for all Anka keywords, functions, and types
- Code snippets for common patterns (pipeline, step, filter, map, etc.)
- Run command (Ctrl+Shift+R) to execute Anka files
- Check command (Ctrl+Shift+C) for syntax validation
- Automatic syntax checking on save
- Hover documentation for keywords and functions
- Autocomplete suggestions for keywords and functions
- Language configuration for comments, brackets, and folding

### Supported Keywords

- Pipeline structure: PIPELINE, INPUT, OUTPUT, STEP
- Data operations: FILTER, SELECT, MAP, SORT, LIMIT, SKIP, DISTINCT, AGGREGATE
- Control flow: IF, ELSE, END, FOR_EACH, WHILE, TRY, ON_ERROR, MATCH, CASE
- I/O operations: READ, WRITE, FETCH, POST
- Statements: SET, APPEND, ASSERT, RETURN, BREAK, CONTINUE

### Supported Functions

- String: UPPER, LOWER, TRIM, LENGTH, SUBSTRING, REPLACE, CONCAT, etc.
- Date: NOW, TODAY, YEAR, MONTH, DAY, ADD_DAYS, FORMAT_DATE, etc.
- Aggregate: SUM, AVG, MIN, MAX, COUNT
- Null handling: COALESCE, IFNULL, IS_NULL, IS_NOT_NULL
