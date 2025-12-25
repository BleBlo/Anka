# Anka Few-Shot Examples

## Task: Filter orders where amount > 200
**Input Schema:**
- orders: [id: INT, customer: STRING, amount: DECIMAL]

**Solution:**
```anka
PIPELINE filter_orders:
  INPUT orders: TABLE[id: INT, customer: STRING, amount: DECIMAL]

  STEP filter_high:
    FILTER orders
    WHERE amount > 200
    INTO high_orders

  OUTPUT high_orders
```

---

## Task: Add a 'tax' column that equals price * 0.08
**Input Schema:**
- products: [id: INT, name: STRING, price: DECIMAL]

**Solution:**
```anka
PIPELINE add_tax:
  INPUT products: TABLE[id: INT, name: STRING, price: DECIMAL]

  STEP compute_tax:
    ADD_COLUMN products
    SET tax = price * 0.08
    INTO taxed_products

  OUTPUT taxed_products
```

---

## Task: Count the total number of users
**Input Schema:**
- users: [id: INT, name: STRING, email: STRING]

**Solution:**
```anka
PIPELINE count_users:
  INPUT users: TABLE[id: INT, name: STRING, email: STRING]

  STEP count_all:
    AGGREGATE users
    COMPUTE user_count = COUNT(*)
    INTO result

  OUTPUT result.user_count
```

---

## Task: Group orders by status and calculate average amount per status
**Input Schema:**
- orders: [id: INT, status: STRING, amount: DECIMAL]

**Solution:**
```anka
PIPELINE avg_by_status:
  INPUT orders: TABLE[id: INT, status: STRING, amount: DECIMAL]

  STEP group_by_status:
    AGGREGATE orders
    GROUP BY status
    COMPUTE avg_amount = AVG(amount)
    INTO status_summary

  OUTPUT status_summary
```

---

## Task: Join products with categories on category_id and select product name and category name
**Input Schema:**
- products: [id: INT, name: STRING, category_id: INT]
- categories: [id: INT, name: STRING]

**Solution:**
```anka
PIPELINE join_products_categories:
  INPUT products: TABLE[id: INT, name: STRING, category_id: INT]
  INPUT categories: TABLE[id: INT, name: STRING]

  STEP join_tables:
    JOIN products WITH categories
    ON products.category_id = categories.id
    INTO joined

  STEP select_names:
    SELECT products.name AS product_name, categories.name AS category_name
    FROM joined
    INTO result

  OUTPUT result
```

---

## Task: Filter users where email contains '@gmail.com'
**Input Schema:**
- users: [id: INT, name: STRING, email: STRING]

**Solution:**
```anka
PIPELINE filter_gmail:
  INPUT users: TABLE[id: INT, name: STRING, email: STRING]

  STEP filter_gmail_users:
    FILTER users
    WHERE CONTAINS(email, "@gmail.com")
    INTO gmail_users

  OUTPUT gmail_users
```

---

## Task: Add a 'priority' column: 'urgent' if days_left < 3, 'normal' if days_left < 7, else 'low'
**Input Schema:**
- tasks: [id: INT, title: STRING, days_left: INT]

**Solution:**
```anka
PIPELINE add_priority:
  INPUT tasks: TABLE[id: INT, title: STRING, days_left: INT]

  STEP compute_priority:
    ADD_COLUMN tasks
    SET priority = IF(days_left < 3, "urgent", IF(days_left < 7, "normal", "low"))
    INTO prioritized_tasks

  OUTPUT prioritized_tasks
```

---

## Task: Sort products by price ascending, then by name alphabetically
**Input Schema:**
- products: [id: INT, name: STRING, price: DECIMAL]

**Solution:**
```anka
PIPELINE sort_products:
  INPUT products: TABLE[id: INT, name: STRING, price: DECIMAL]

  STEP sort_by_price:
    SORT products
    BY price ASC, name ASC
    INTO sorted_products

  OUTPUT sorted_products
```

---

## Task: Calculate total revenue (sum of price * quantity)
**Input Schema:**
- orders: [id: INT, price: DECIMAL, quantity: INT]

**Solution:**
```anka
PIPELINE total_revenue:
  INPUT orders: TABLE[id: INT, price: DECIMAL, quantity: INT]

  STEP add_line_total:
    ADD_COLUMN orders
    SET line_total = price * quantity
    INTO orders_with_total

  STEP sum_revenue:
    AGGREGATE orders_with_total
    COMPUTE total = SUM(line_total)
    INTO result

  OUTPUT result.total
```

---

## Task: Filter active orders and group by customer with order count
**Input Schema:**
- orders: [id: INT, customer: STRING, status: STRING, amount: DECIMAL]

**Solution:**
```anka
PIPELINE active_orders_by_customer:
  INPUT orders: TABLE[id: INT, customer: STRING, status: STRING, amount: DECIMAL]

  STEP filter_active:
    FILTER orders
    WHERE status = "active"
    INTO active_orders

  STEP group_by_customer:
    AGGREGATE active_orders
    GROUP BY customer
    COMPUTE order_count = COUNT(*), total_amount = SUM(amount)
    INTO customer_summary

  OUTPUT customer_summary
```
