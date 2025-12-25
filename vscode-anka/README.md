# Anka Language Support for VS Code

Language support for **Anka** - the LLM-optimized data transformation DSL.

## Features

### Syntax Highlighting

Full syntax highlighting for all Anka constructs:
- Keywords (PIPELINE, STEP, FILTER, SELECT, MAP, etc.)
- Built-in functions (UPPER, LOWER, NOW, SUM, etc.)
- Types (TABLE, INT, STRING, DECIMAL, BOOL)
- Strings, numbers, and comments

### Code Snippets

Quick snippets for common patterns:
- `pipeline` - Create a new pipeline
- `step` - Add a step
- `filter` - FILTER operation
- `select` - SELECT operation
- `map` - MAP operation
- `sort` - SORT operation
- `aggregate` - AGGREGATE with GROUP_BY
- `if` - IF-ELSE block
- `foreach` - FOR_EACH loop
- `try` - TRY-ON_ERROR block
- `fetch` - HTTP FETCH request
- `readjson` - Read JSON file
- `writejson` - Write JSON file

### Commands

- **Anka: Run Pipeline** (`Ctrl+Shift+R` / `Cmd+Shift+R`) - Execute the current file
- **Anka: Check Syntax** (`Ctrl+Shift+C` / `Cmd+Shift+C`) - Validate syntax

### Diagnostics

- Automatic syntax checking on save
- Error squiggles with line/column information

### Hover Documentation

Hover over keywords and functions to see documentation.

### Autocomplete

Get suggestions for keywords and functions as you type.

## Requirements

- Python 3.11+ with Anka installed
- `python -m anka` must be available in PATH

## Extension Settings

- `anka.pythonPath`: Path to Python interpreter (default: `python`)
- `anka.checkOnSave`: Run syntax check on save (default: `true`)
- `anka.showHoverDocumentation`: Show docs on hover (default: `true`)

## Example Anka Code

```anka
PIPELINE sales_report:
    INPUT sales: TABLE[product: STRING, quantity: INT, price: DECIMAL]

    STEP filter_valid:
        FILTER sales
        WHERE quantity > 0
        INTO valid_sales

    STEP add_total:
        MAP valid_sales
        WITH total => quantity * price
        INTO with_totals

    STEP top_sellers:
        SORT with_totals
        BY total DESC
        INTO sorted

    STEP top_five:
        LIMIT sorted
        COUNT 5
        INTO top_sales

    OUTPUT top_sales
```

## Installation

### From VSIX

1. Download the `.vsix` file
2. Open VS Code
3. Press `Ctrl+Shift+P` and run "Extensions: Install from VSIX..."
4. Select the downloaded file

### From Source

```bash
cd vscode-anka
npm install
npm run compile
npm run package
```

## Links

- [Anka Repository](https://github.com/BleBlo/Anka)
- [Report Issues](https://github.com/BleBlo/Anka/issues)

## License

MIT
