# DSL Viability Study: Methodology

## Research Questions

1. **RQ1:** Can LLMs effectively learn and generate code in a novel DSL taught entirely via prompt?

2. **RQ2:** Does constrained DSL syntax result in higher parse success rates compared to flexible syntax?

3. **RQ3:** What proportion of DSL errors are automatically recoverable due to predictable syntax?

4. **RQ4:** Does constrained syntax improve output consistency across multiple samples?

## Important Note on Comparison Fairness

This study does NOT claim that Anka is "better" than Python for LLM code generation. Such a comparison would be fundamentally unfair because:

- **Python**: LLMs have been trained on billions of Python examples
- **Anka**: LLMs have zero prior exposure; all knowledge comes from the prompt

Instead, we study:
1. Whether prompt-based DSL teaching is viable
2. What properties emerge from constrained syntax (recoverability, consistency)
3. How a novel DSL compares to native language knowledge as a baseline

## Experimental Design

### Independent Variables
- Language: Anka (novel DSL) vs Python (native knowledge baseline)

### Dependent Variables
1. **Parse Success Rate**: % of generated code that parses successfully
2. **Overall Accuracy**: % of samples that pass all test cases
3. **Recovery Rate**: % of parse failures that can be automatically fixed
4. **Effective Accuracy**: Accuracy after applying automatic recovery
5. **Consistency Score**: Agreement across multiple samples for same task

### Controlled Variables
- Same LLM model for paired comparisons
- Same task descriptions for both languages
- Same test cases and expected outputs
- Same temperature setting (0.7)
- Same number of samples per task (10)

## Tasks

- **Total**: 70+ tasks across 6 categories
- **Categories**: filter, map, aggregate, strings, multi_step, complex
- **Test Cases**: 2-3 per task, including edge cases
- **Difficulty**: Easy (single operation) to Hard (5+ step pipelines)

## Error Recovery System

Anka's constrained syntax enables automatic error recovery:

1. **Missing INTO clause**: Auto-append `INTO result_N`
2. **Wrong equality operator**: Replace `=` with `==` in conditions
3. **Missing source table**: Infer from INPUT declaration

Recovery is NOT attempted for Python because:
- Python's flexible syntax makes error patterns unpredictable
- Auto-fixing Python could introduce subtle bugs
- This asymmetry is intentional and reported as a DSL advantage

## Statistical Analysis

1. **Confidence Intervals**: Wilson score (better for proportions)
2. **Significance Test**: McNemar's test (paired nominal data)
3. **Effect Size**: Cohen's h (proportion comparison)
4. **Per-Category Breakdown**: To identify where DSL helps most

## Reproducibility

All materials available in repository:
- Task definitions: `benchmarks/tasks/`
- Prompts: `benchmarks/prompts/`
- Runner code: `benchmarks/runner_detailed.py`
- Analysis code: `benchmarks/publication_stats.py`
- Results: `benchmarks/results/`

## Limitations

1. Single domain (data transformations)
2. Limited LLM models tested
3. Prompt quality affects results
4. Recovery system is Anka-specific by design

## Ethical Considerations

- No human subjects
- Open-source release enables verification
- Honest reporting of comparison limitations
