import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

// Diagnostic collection for syntax errors
let diagnosticCollection: vscode.DiagnosticCollection;

// Documentation for keywords and functions
const KEYWORD_DOCS: { [key: string]: string } = {
    // Pipeline structure
    'PIPELINE': 'Defines a new data transformation pipeline.\n\nSyntax: `PIPELINE name:`',
    'INPUT': 'Declares an input table with its schema.\n\nSyntax: `INPUT name: TABLE[field: TYPE, ...]`',
    'OUTPUT': 'Specifies the output of the pipeline.\n\nSyntax: `OUTPUT table_name`',
    'STEP': 'Defines a named step in the pipeline.\n\nSyntax: `STEP name: operation`',

    // Data operations
    'FILTER': 'Filters rows based on a condition.\n\nSyntax: `FILTER source WHERE condition INTO target`',
    'SELECT': 'Selects specific columns from a table.\n\nSyntax: `SELECT col1, col2 FROM source INTO target`',
    'MAP': 'Adds computed columns to a table.\n\nSyntax: `MAP source WITH new_col => expression INTO target`',
    'SORT': 'Sorts rows by a column.\n\nSyntax: `SORT source BY column ASC|DESC INTO target`',
    'LIMIT': 'Takes the first N rows.\n\nSyntax: `LIMIT source COUNT n INTO target`',
    'SKIP': 'Skips the first N rows.\n\nSyntax: `SKIP source COUNT n INTO target`',
    'DISTINCT': 'Removes duplicate rows.\n\nSyntax: `DISTINCT source BY columns INTO target`',
    'AGGREGATE': 'Groups and aggregates data.\n\nSyntax: `AGGREGATE source GROUP_BY cols COMPUTE agg_funcs INTO target`',

    // Control flow
    'IF': 'Conditional execution.\n\nSyntax: `IF condition: ... ELSE: ... END`',
    'ELSE': 'Alternative branch in IF statement.',
    'END': 'Ends a control flow block (IF, FOR_EACH, WHILE, TRY, MATCH).',
    'FOR_EACH': 'Iterates over a collection.\n\nSyntax: `FOR_EACH item IN collection: ... END`',
    'WHILE': 'Loop while condition is true.\n\nSyntax: `WHILE condition: ... END`',
    'TRY': 'Error handling block.\n\nSyntax: `TRY: ... ON_ERROR: ... END`',
    'ON_ERROR': 'Error handler in TRY block.',
    'MATCH': 'Pattern matching.\n\nSyntax: `MATCH var: CASE val: ... DEFAULT: ... END`',
    'CASE': 'A case in MATCH statement.',
    'DEFAULT': 'Default case in MATCH statement.',

    // Statements
    'SET': 'Assigns a value to a variable.\n\nSyntax: `SET variable = expression`',
    'APPEND': 'Adds an item to a collection.\n\nSyntax: `APPEND item TO collection`',
    'ASSERT': 'Validates a condition.\n\nSyntax: `ASSERT condition MESSAGE "error text"`',
    'RETURN': 'Returns early from pipeline.',
    'BREAK': 'Exits a loop early.',
    'CONTINUE': 'Skips to next loop iteration.',

    // I/O
    'READ': 'Reads data from a file.\n\nSyntax: `READ "path" FORMAT JSON|CSV INTO target`',
    'WRITE': 'Writes data to a file.\n\nSyntax: `WRITE source TO "path" FORMAT JSON|CSV`',
    'FETCH': 'Makes an HTTP request.\n\nSyntax: `FETCH "url" METHOD GET|POST|PUT|DELETE INTO target`',
    'POST': 'Makes an HTTP POST request.\n\nSyntax: `POST "url" BODY data INTO target`',

    // Clauses
    'WHERE': 'Specifies a filter condition.',
    'INTO': 'Specifies the output variable.',
    'FROM': 'Specifies the source table.',
    'BY': 'Specifies grouping or sorting column.',
    'WITH': 'Specifies computed column in MAP.',
    'AS': 'Specifies alias name.',
    'TO': 'Specifies destination.',
    'IN': 'Checks membership or specifies iteration source.',
    'COUNT': 'Specifies number of rows or count aggregate.',
    'GROUP_BY': 'Specifies grouping columns.',
    'COMPUTE': 'Specifies aggregate computations.',
    'ASC': 'Ascending sort order.',
    'DESC': 'Descending sort order.',
    'NULLS_FIRST': 'Sort nulls before other values.',
    'NULLS_LAST': 'Sort nulls after other values.',

    // Logical
    'AND': 'Logical AND operator.',
    'OR': 'Logical OR operator.',
    'NOT': 'Logical NOT operator.',
    'BETWEEN': 'Range check.\n\nSyntax: `column BETWEEN low AND high`',

    // Types
    'TABLE': 'Table type.\n\nSyntax: `TABLE[field: TYPE, ...]`',
    'INT': 'Integer type.',
    'STRING': 'String type.',
    'DECIMAL': 'Decimal number type.',
    'BOOL': 'Boolean type.',
    'DATE': 'Date type.',
    'DATETIME': 'Date and time type.',

    // Format types
    'JSON': 'JSON file format.',
    'CSV': 'CSV file format.',

    // HTTP methods
    'METHOD': 'HTTP method specification.',
    'HEADERS': 'HTTP headers.\n\nSyntax: `HEADERS {"key": "value"}`',
    'BODY': 'HTTP request body.',
    'GET': 'HTTP GET method.',
    'PUT': 'HTTP PUT method.',
    'DELETE': 'HTTP DELETE method.',
};

const FUNCTION_DOCS: { [key: string]: string } = {
    // String functions
    'UPPER': 'Converts string to uppercase.\n\nSyntax: `UPPER(string)`',
    'LOWER': 'Converts string to lowercase.\n\nSyntax: `LOWER(string)`',
    'TRIM': 'Removes whitespace from both ends.\n\nSyntax: `TRIM(string)`',
    'LTRIM': 'Removes whitespace from left.\n\nSyntax: `LTRIM(string)`',
    'RTRIM': 'Removes whitespace from right.\n\nSyntax: `RTRIM(string)`',
    'LENGTH': 'Returns string length.\n\nSyntax: `LENGTH(string)`',
    'REVERSE': 'Reverses a string.\n\nSyntax: `REVERSE(string)`',
    'SUBSTRING': 'Extracts a substring.\n\nSyntax: `SUBSTRING(string, start, length)`',
    'LEFT': 'Returns leftmost characters.\n\nSyntax: `LEFT(string, count)`',
    'RIGHT': 'Returns rightmost characters.\n\nSyntax: `RIGHT(string, count)`',
    'INDEX_OF': 'Finds position of substring.\n\nSyntax: `INDEX_OF(string, search)`',
    'REPLACE': 'Replaces first occurrence.\n\nSyntax: `REPLACE(string, old, new)`',
    'REPLACE_ALL': 'Replaces all occurrences.\n\nSyntax: `REPLACE_ALL(string, old, new)`',
    'PAD_LEFT': 'Pads string on left.\n\nSyntax: `PAD_LEFT(string, length, char)`',
    'PAD_RIGHT': 'Pads string on right.\n\nSyntax: `PAD_RIGHT(string, length, char)`',
    'REPEAT': 'Repeats a string.\n\nSyntax: `REPEAT(string, count)`',
    'CONCAT': 'Concatenates strings.\n\nSyntax: `CONCAT(str1, str2, ...)`',

    // String checks
    'CONTAINS': 'Checks if string contains substring.\n\nSyntax: `CONTAINS(column, "text")`',
    'STARTS_WITH': 'Checks if string starts with prefix.\n\nSyntax: `STARTS_WITH(column, "prefix")`',
    'ENDS_WITH': 'Checks if string ends with suffix.\n\nSyntax: `ENDS_WITH(column, "suffix")`',
    'MATCHES': 'Checks if string matches regex.\n\nSyntax: `MATCHES(column, "pattern")`',

    // Date functions
    'NOW': 'Returns current datetime.\n\nSyntax: `NOW()`',
    'TODAY': 'Returns current date.\n\nSyntax: `TODAY()`',
    'YEAR': 'Extracts year from date.\n\nSyntax: `YEAR(date)`',
    'MONTH': 'Extracts month from date.\n\nSyntax: `MONTH(date)`',
    'DAY': 'Extracts day from date.\n\nSyntax: `DAY(date)`',
    'HOUR': 'Extracts hour from datetime.\n\nSyntax: `HOUR(datetime)`',
    'MINUTE': 'Extracts minute from datetime.\n\nSyntax: `MINUTE(datetime)`',
    'SECOND': 'Extracts second from datetime.\n\nSyntax: `SECOND(datetime)`',
    'DAY_OF_WEEK': 'Returns day of week (0-6).\n\nSyntax: `DAY_OF_WEEK(date)`',
    'WEEK_OF_YEAR': 'Returns week number.\n\nSyntax: `WEEK_OF_YEAR(date)`',
    'ADD_DAYS': 'Adds days to date.\n\nSyntax: `ADD_DAYS(date, count)`',
    'ADD_MONTHS': 'Adds months to date.\n\nSyntax: `ADD_MONTHS(date, count)`',
    'ADD_YEARS': 'Adds years to date.\n\nSyntax: `ADD_YEARS(date, count)`',
    'ADD_HOURS': 'Adds hours to datetime.\n\nSyntax: `ADD_HOURS(datetime, count)`',
    'DIFF_DAYS': 'Returns days between dates.\n\nSyntax: `DIFF_DAYS(date1, date2)`',
    'PARSE_DATE': 'Parses string to date.\n\nSyntax: `PARSE_DATE(string, "format")`',
    'FORMAT_DATE': 'Formats date to string.\n\nSyntax: `FORMAT_DATE(date, "format")`',

    // Date checks
    'IS_BEFORE': 'Checks if date is before another.\n\nSyntax: `IS_BEFORE(column, date)`',
    'IS_AFTER': 'Checks if date is after another.\n\nSyntax: `IS_AFTER(column, date)`',
    'IS_WEEKEND': 'Checks if date is weekend.\n\nSyntax: `IS_WEEKEND(column)`',

    // Aggregate functions
    'SUM': 'Sums values.\n\nSyntax: `SUM(column)`',
    'AVG': 'Averages values.\n\nSyntax: `AVG(column)`',
    'MIN': 'Finds minimum value.\n\nSyntax: `MIN(column)`',
    'MAX': 'Finds maximum value.\n\nSyntax: `MAX(column)`',

    // Null functions
    'COALESCE': 'Returns first non-null value.\n\nSyntax: `COALESCE(column, default)`',
    'IFNULL': 'Returns default if null.\n\nSyntax: `IFNULL(column, default)`',
    'IS_NULL': 'Checks if value is null.\n\nSyntax: `column IS_NULL`',
    'IS_NOT_NULL': 'Checks if value is not null.\n\nSyntax: `column IS_NOT_NULL`',
};

// All keywords and functions for completion
const ALL_KEYWORDS = Object.keys(KEYWORD_DOCS);
const ALL_FUNCTIONS = Object.keys(FUNCTION_DOCS);

export function activate(context: vscode.ExtensionContext) {
    console.log('Anka Language extension is now active');

    // Create diagnostic collection
    diagnosticCollection = vscode.languages.createDiagnosticCollection('anka');
    context.subscriptions.push(diagnosticCollection);

    // Register run command
    const runCommand = vscode.commands.registerCommand('anka.run', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'anka') {
            vscode.window.showErrorMessage('Please open an Anka file first');
            return;
        }

        await editor.document.save();
        const filePath = editor.document.uri.fsPath;

        // Ask for input file
        const inputFile = await vscode.window.showInputBox({
            prompt: 'Enter path to input JSON file (or leave empty for no input)',
            placeHolder: 'data.json'
        });

        runAnkaFile(filePath, inputFile || undefined);
    });

    // Register check command
    const checkCommand = vscode.commands.registerCommand('anka.check', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'anka') {
            vscode.window.showErrorMessage('Please open an Anka file first');
            return;
        }

        await editor.document.save();
        checkAnkaFile(editor.document);
    });

    // Register format command (placeholder)
    const formatCommand = vscode.commands.registerCommand('anka.format', () => {
        vscode.window.showInformationMessage('Anka formatting is not yet implemented');
    });

    // Register check syntax command
    const checkSyntaxCommand = vscode.commands.registerCommand('anka.checkSyntax', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'anka') {
            vscode.window.showErrorMessage('Please open an Anka file first');
            return;
        }

        await editor.document.save();
        checkAnkaFile(editor.document);
    });

    // Check on save
    const onSave = vscode.workspace.onDidSaveTextDocument((document) => {
        if (document.languageId === 'anka') {
            const config = vscode.workspace.getConfiguration('anka');
            if (config.get('checkOnSave', true)) {
                checkAnkaFile(document);
            }
        }
    });

    // Register hover provider
    const hoverProvider = vscode.languages.registerHoverProvider('anka', {
        provideHover(document, position) {
            const config = vscode.workspace.getConfiguration('anka');
            if (!config.get('showHoverDocumentation', true)) {
                return undefined;
            }

            const range = document.getWordRangeAtPosition(position, /[A-Z_]+/);
            if (!range) {
                return undefined;
            }

            const word = document.getText(range);

            if (KEYWORD_DOCS[word]) {
                return new vscode.Hover(
                    new vscode.MarkdownString(`**${word}** (keyword)\n\n${KEYWORD_DOCS[word]}`)
                );
            }

            if (FUNCTION_DOCS[word]) {
                return new vscode.Hover(
                    new vscode.MarkdownString(`**${word}** (function)\n\n${FUNCTION_DOCS[word]}`)
                );
            }

            return undefined;
        }
    });

    // Register completion provider
    const completionProvider = vscode.languages.registerCompletionItemProvider('anka', {
        provideCompletionItems(document, position) {
            const completions: vscode.CompletionItem[] = [];

            // Add keywords
            for (const keyword of ALL_KEYWORDS) {
                const item = new vscode.CompletionItem(keyword, vscode.CompletionItemKind.Keyword);
                item.detail = 'Anka keyword';
                item.documentation = new vscode.MarkdownString(KEYWORD_DOCS[keyword]);
                completions.push(item);
            }

            // Add functions
            for (const func of ALL_FUNCTIONS) {
                const item = new vscode.CompletionItem(func, vscode.CompletionItemKind.Function);
                item.detail = 'Anka function';
                item.documentation = new vscode.MarkdownString(FUNCTION_DOCS[func]);
                // Add parentheses for functions
                if (!['IS_NULL', 'IS_NOT_NULL'].includes(func)) {
                    item.insertText = new vscode.SnippetString(`${func}($1)`);
                }
                completions.push(item);
            }

            return completions;
        }
    });

    context.subscriptions.push(
        runCommand,
        checkCommand,
        formatCommand,
        checkSyntaxCommand,
        onSave,
        hoverProvider,
        completionProvider
    );
}

function getPythonPath(): string {
    const config = vscode.workspace.getConfiguration('anka');
    return config.get('pythonPath', 'python');
}

function runAnkaFile(filePath: string, inputFile?: string) {
    const pythonPath = getPythonPath();
    const outputChannel = vscode.window.createOutputChannel('Anka');
    outputChannel.show();
    outputChannel.clear();

    let command: string;
    if (inputFile) {
        // Resolve input file path relative to the anka file
        const ankaDir = path.dirname(filePath);
        const resolvedInputPath = path.isAbsolute(inputFile)
            ? inputFile
            : path.join(ankaDir, inputFile);
        command = `"${pythonPath}" -m anka run "${filePath}" "${resolvedInputPath}" --json`;
    } else {
        command = `"${pythonPath}" -m anka parse "${filePath}"`;
    }

    outputChannel.appendLine(`Running: ${command}\n`);

    cp.exec(command, { cwd: vscode.workspace.rootPath }, (error, stdout, stderr) => {
        if (stdout) {
            try {
                // Try to parse and pretty-print JSON output
                const json = JSON.parse(stdout);
                outputChannel.appendLine(JSON.stringify(json, null, 2));
            } catch {
                outputChannel.appendLine(stdout);
            }
        }
        if (stderr) {
            outputChannel.appendLine(`Error: ${stderr}`);
        }
        if (error) {
            outputChannel.appendLine(`Exit code: ${error.code}`);
        }
    });
}

function checkAnkaFile(document: vscode.TextDocument) {
    const pythonPath = getPythonPath();
    const filePath = document.uri.fsPath;
    const command = `"${pythonPath}" -m anka check "${filePath}" --json`;

    cp.exec(command, { cwd: vscode.workspace.rootPath }, (error, stdout, stderr) => {
        const diagnostics: vscode.Diagnostic[] = [];

        if (stdout) {
            try {
                const result = JSON.parse(stdout);
                if (result.status === 'ok') {
                    vscode.window.showInformationMessage('Anka: No syntax errors');
                } else if (result.errors && result.errors.length > 0) {
                    for (const err of result.errors) {
                        const line = Math.max(0, (err.line || 1) - 1);
                        const column = Math.max(0, (err.column || 1) - 1);
                        const range = new vscode.Range(line, column, line, column + 10);
                        const diagnostic = new vscode.Diagnostic(
                            range,
                            err.message,
                            vscode.DiagnosticSeverity.Error
                        );
                        diagnostic.source = 'anka';
                        diagnostics.push(diagnostic);
                    }
                }
            } catch {
                // JSON parse failed, try to extract error from stderr
                if (stderr) {
                    const range = new vscode.Range(0, 0, 0, 10);
                    diagnostics.push(new vscode.Diagnostic(
                        range,
                        stderr,
                        vscode.DiagnosticSeverity.Error
                    ));
                }
            }
        }

        if (error && diagnostics.length === 0) {
            // Fallback error handling
            const errorMessage = stderr || 'Unknown error occurred';
            const range = new vscode.Range(0, 0, 0, 10);
            diagnostics.push(new vscode.Diagnostic(
                range,
                errorMessage,
                vscode.DiagnosticSeverity.Error
            ));
        }

        diagnosticCollection.set(document.uri, diagnostics);
    });
}

export function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
    }
}
