
## Benchmark Results

### Accuracy by Category (Claude 3.5 Haiku)

| Category | Anka | Python | Delta | Winner |
|----------|------|--------|-------|--------|
| **multi_step** | **100.0%** | 60.0% | **+40.0%** | **Anka** |
| finance | **90.0%** | 85.0% | +5.0% | **Anka** |
| aggregate | 100.0% | 100.0% | 0.0% | Tie |
| filter | 96.7% | 100.0% | -3.3% | Python |
| map | 100.0% | 100.0% | 0.0% | Tie |
| strings | 100.0% | 100.0% | 0.0% | Tie |
| hard | 90.0% | 100.0% | -10.0% | Python |
| **Overall** | **95.8%** | 91.2% | **+4.6%** | **Anka** |

### Key Findings

1. **Multi-step pipelines**: Anka achieves **40% higher accuracy** than Python (100% vs 60%)
2. **Parse success**: 99.9% of generated Anka code parses successfully
3. **Novel DSL**: Anka learned entirely from prompt (zero training data)
4. **Overall**: Anka outperforms Python by **4.6 percentage points**

### Why Anka Wins on Multi-Step Tasks

Python fails on multi-step tasks due to:
- Variable shadowing and naming conflicts
- Incorrect operation sequencing
- Missing intermediate state management

Anka's explicit pipeline syntax prevents these errors:
```
STEP filter_active:
    FILTER orders WHERE status == "active" INTO active_orders

STEP join_customers:
    JOIN active_orders WITH customers ON customer_id == id INTO joined

STEP aggregate:
    AGGREGATE joined GROUP_BY region COMPUTE SUM(amount) AS total INTO summary
```

Each step is explicit, named, and connected through `INTO` clauses.
