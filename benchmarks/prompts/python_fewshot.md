# Python Few-Shot Examples

## Task: Filter orders where amount > 200
**Input Schema:**
- orders: [id: INT, customer: STRING, amount: DECIMAL]

**Solution:**
```python
def transform(data: dict):
    orders = data["orders"]
    return [row for row in orders if row["amount"] > 200]
```

---

## Task: Add a 'tax' column that equals price * 0.08
**Input Schema:**
- products: [id: INT, name: STRING, price: DECIMAL]

**Solution:**
```python
def transform(data: dict):
    products = data["products"]
    result = []
    for row in products:
        new_row = dict(row)
        new_row["tax"] = row["price"] * 0.08
        result.append(new_row)
    return result
```

---

## Task: Count the total number of users. Return a list with one record containing 'count' field.
**Input Schema:**
- users: [id: INT, name: STRING, email: STRING]

**Solution:**
```python
def transform(data: dict):
    return [{"count": len(data["users"])}]
```

---

## Task: Calculate the total sum of the amount column. Return a list with one record containing 'total' field.
**Input Schema:**
- orders: [id: INT, customer: STRING, amount: DECIMAL]

**Solution:**
```python
def transform(data: dict):
    orders = data["orders"]
    total = sum(row["amount"] for row in orders)
    return [{"total": total}]
```

---

## Task: Group orders by status and calculate average amount per status
**Input Schema:**
- orders: [id: INT, status: STRING, amount: DECIMAL]

**Solution:**
```python
def transform(data: dict):
    orders = data["orders"]
    groups = {}
    for row in orders:
        status = row["status"]
        if status not in groups:
            groups[status] = []
        groups[status].append(row["amount"])

    result = []
    for status, amounts in groups.items():
        result.append({
            "status": status,
            "avg_amount": sum(amounts) / len(amounts)
        })
    return result
```

---

## Task: Join products with categories on category_id and select product name and category name
**Input Schema:**
- products: [id: INT, name: STRING, category_id: INT]
- categories: [id: INT, name: STRING]

**Solution:**
```python
def transform(data: dict):
    products = data["products"]
    categories = data["categories"]

    cat_lookup = {c["id"]: c["name"] for c in categories}

    result = []
    for prod in products:
        result.append({
            "product_name": prod["name"],
            "category_name": cat_lookup.get(prod["category_id"], None)
        })
    return result
```

---

## Task: Filter users where email contains '@gmail.com'
**Input Schema:**
- users: [id: INT, name: STRING, email: STRING]

**Solution:**
```python
def transform(data: dict):
    users = data["users"]
    return [row for row in users if "@gmail.com" in row["email"]]
```

---

## Task: Add a 'priority' column: 'urgent' if days_left < 3, 'normal' if days_left < 7, else 'low'
**Input Schema:**
- tasks: [id: INT, title: STRING, days_left: INT]

**Solution:**
```python
def transform(data: dict):
    tasks = data["tasks"]
    result = []
    for row in tasks:
        new_row = dict(row)
        if row["days_left"] < 3:
            new_row["priority"] = "urgent"
        elif row["days_left"] < 7:
            new_row["priority"] = "normal"
        else:
            new_row["priority"] = "low"
        result.append(new_row)
    return result
```

---

## Task: Sort products by price ascending, then by name alphabetically
**Input Schema:**
- products: [id: INT, name: STRING, price: DECIMAL]

**Solution:**
```python
def transform(data: dict):
    products = data["products"]
    return sorted(products, key=lambda x: (x["price"], x["name"]))
```
