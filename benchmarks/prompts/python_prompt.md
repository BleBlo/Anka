# Python Data Transformation Reference

You are a Python expert. Given a data transformation task, write Python code to solve it.

## Input Format
- Data is provided as a dictionary of lists of dictionaries (JSON-like structure)
- Each key in the input dictionary is a table name
- Each table is a list of row dictionaries

## Output Requirements
- Your code MUST define a `transform(data: dict) -> Any` function
- The function receives the input data and returns the result
- Return type depends on the task (list of dicts, scalar, single dict, etc.)
- Use only Python standard library (no pandas, numpy, etc.)

## Examples

### Example 1: Filter rows
```python
def transform(data: dict):
    """Filter orders where amount > 100"""
    orders = data["orders"]
    return [row for row in orders if row["amount"] > 100]
```

### Example 2: Add computed column
```python
def transform(data: dict):
    """Add a 'total' column = price * quantity"""
    orders = data["orders"]
    result = []
    for row in orders:
        new_row = dict(row)
        new_row["total"] = row["price"] * row["quantity"]
        result.append(new_row)
    return result
```

### Example 3: Aggregate (SUM)
```python
def transform(data: dict):
    """Calculate total amount"""
    orders = data["orders"]
    return sum(row["amount"] for row in orders)
```

### Example 4: Group by with aggregation
```python
def transform(data: dict):
    """Group by customer and sum amounts"""
    orders = data["orders"]
    groups = {}
    for row in orders:
        key = row["customer"]
        if key not in groups:
            groups[key] = 0
        groups[key] += row["amount"]
    return [{"customer": k, "total": v} for k, v in groups.items()]
```

### Example 5: Join two tables
```python
def transform(data: dict):
    """Join orders with customers on customer_id"""
    orders = data["orders"]
    customers = data["customers"]

    # Create lookup
    customer_lookup = {c["id"]: c for c in customers}

    result = []
    for order in orders:
        customer = customer_lookup.get(order["customer_id"], {})
        merged = dict(order)
        for k, v in customer.items():
            if k != "id":  # Don't duplicate id
                merged[k] = v
        result.append(merged)
    return result
```

### Example 6: String operations
```python
def transform(data: dict):
    """Add uppercase name column"""
    users = data["users"]
    result = []
    for row in users:
        new_row = dict(row)
        new_row["name_upper"] = row["name"].upper()
        result.append(new_row)
    return result
```

### Example 7: Conditional column
```python
def transform(data: dict):
    """Add category based on amount"""
    orders = data["orders"]
    result = []
    for row in orders:
        new_row = dict(row)
        if row["amount"] > 500:
            new_row["category"] = "high"
        elif row["amount"] > 100:
            new_row["category"] = "medium"
        else:
            new_row["category"] = "low"
        result.append(new_row)
    return result
```

### Example 8: Sort data
```python
def transform(data: dict):
    """Sort products by price descending"""
    products = data["products"]
    return sorted(products, key=lambda x: x["price"], reverse=True)
```

### Example 9: Filter with multiple conditions
```python
def transform(data: dict):
    """Filter where status='active' AND amount > 100"""
    orders = data["orders"]
    return [row for row in orders
            if row["status"] == "active" and row["amount"] > 100]
```

### Example 10: Null handling
```python
def transform(data: dict):
    """Use nickname if available, else use name"""
    users = data["users"]
    result = []
    for row in users:
        new_row = dict(row)
        new_row["display_name"] = row["nickname"] if row["nickname"] else row["name"]
        result.append(new_row)
    return result
```

## Common Patterns

### Filtering
```python
[row for row in table if condition]
```

### Mapping (adding columns)
```python
result = []
for row in table:
    new_row = dict(row)
    new_row["new_col"] = expression
    result.append(new_row)
return result
```

### Aggregation
```python
sum(row["col"] for row in table)
len(table)
max(row["col"] for row in table)
min(row["col"] for row in table)
sum(...) / len(table)  # average
```

### Group by
```python
groups = {}
for row in table:
    key = row["group_col"]
    if key not in groups:
        groups[key] = []
    groups[key].append(row)
# Then aggregate each group
```

### Sorting
```python
sorted(table, key=lambda x: x["col"])  # ascending
sorted(table, key=lambda x: x["col"], reverse=True)  # descending
```

### String functions
```python
s.upper()           # uppercase
s.lower()           # lowercase
s.strip()           # trim whitespace
s.replace(a, b)     # replace
len(s)              # length
s[start:end]        # substring
a + b               # concatenation
needle in s         # contains
s.startswith(p)     # starts with
s.endswith(p)       # ends with
```

## Important Notes
- Always define the `transform(data: dict)` function
- Use only standard library (no external packages)
- Handle None/null values appropriately
- Preserve column order when possible
- Return the correct type (list, dict, scalar) based on the task

---

## Your Task

**Task:** {description}

**Input Schema:**
{input_schema}

Write ONLY the Python code (just the `transform` function). No explanation.
