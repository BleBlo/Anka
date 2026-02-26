#!/usr/bin/env python3
"""
Comprehensive metrics for DSL viability study.
Measures more than just pass/fail - captures parse success, recovery, consistency.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import json
import re


@dataclass
class DetailedResult:
    """Detailed result for a single benchmark run."""
    task_id: str
    language: str
    model: str
    sample: int

    # Stage 1: Code Generation
    generated_code: str
    generation_time_ms: int

    # Stage 2: Parsing
    parse_success: bool
    parse_error: Optional[str] = None
    parse_error_type: Optional[str] = None  # syntax, unknown_keyword, missing_clause, etc.

    # Stage 3: Recovery Attempt (if parse failed)
    recovery_attempted: bool = False
    recovery_success: bool = False
    recovered_code: Optional[str] = None
    recovery_method: Optional[str] = None  # alias, auto_fix, etc.

    # Stage 4: Execution (if parse succeeded or recovery succeeded)
    execution_success: bool = False
    execution_error: Optional[str] = None
    execution_time_ms: Optional[int] = None

    # Stage 5: Output Comparison
    output_correct: bool = False
    actual_output: Optional[list] = None
    expected_output: Optional[list] = None
    output_diff: Optional[str] = None

    # Final Status
    @property
    def final_status(self) -> str:
        if self.output_correct:
            return "pass"
        elif not self.parse_success and not self.recovery_success:
            return "parse_error"
        elif not self.execution_success:
            return "runtime_error"
        else:
            return "wrong_output"

    @property
    def passed(self) -> bool:
        return self.output_correct

    @property
    def passed_after_recovery(self) -> bool:
        return self.output_correct and self.recovery_attempted


@dataclass
class TaskMetrics:
    """Aggregated metrics for a single task across all samples."""
    task_id: str
    category: str
    num_samples: int

    # Pass rates
    pass_count: int = 0
    pass_rate: float = 0.0

    # Parse metrics
    parse_success_count: int = 0
    parse_success_rate: float = 0.0

    # Recovery metrics
    recovery_attempted_count: int = 0
    recovery_success_count: int = 0
    recovery_rate: float = 0.0

    # Consistency (do all samples produce same output?)
    unique_outputs: int = 0
    consistency_score: float = 0.0  # 1.0 = all samples same, 0.0 = all different

    # Error breakdown
    parse_errors: int = 0
    runtime_errors: int = 0
    wrong_outputs: int = 0


@dataclass
class LanguageMetrics:
    """Aggregated metrics for a language across all tasks."""
    language: str
    model: str
    total_samples: int
    total_tasks: int

    # Primary metrics
    overall_pass_rate: float = 0.0
    overall_pass_count: int = 0

    # Parse success (KEY METRIC for DSL study)
    parse_success_rate: float = 0.0
    parse_success_count: int = 0

    # Recovery (KEY METRIC for DSL study)
    recovery_eligible_count: int = 0  # samples that failed parsing
    recovery_attempted_count: int = 0
    recovery_success_count: int = 0
    recovery_rate: float = 0.0  # of eligible, how many recovered
    pass_rate_with_recovery: float = 0.0  # effective pass rate after recovery

    # Execution success (given successful parse)
    execution_success_rate: float = 0.0

    # Output correctness (given successful execution)
    output_correct_rate: float = 0.0

    # Consistency
    avg_consistency_score: float = 0.0
    fully_consistent_tasks: int = 0  # tasks where all samples agree

    # Error breakdown
    parse_error_count: int = 0
    runtime_error_count: int = 0
    wrong_output_count: int = 0

    # By category
    metrics_by_category: dict = field(default_factory=dict)


def classify_parse_error(error_message: str, code: str, language: str) -> str:
    """Classify parse error into categories for analysis."""
    error_lower = error_message.lower()
    code_lower = code.lower()

    if language == 'anka':
        if 'into' not in code_lower and ('filter' in code_lower or 'map' in code_lower or 'sort' in code_lower):
            return 'missing_into'
        elif 'unexpected' in error_lower:
            return 'syntax_error'
        elif 'unknown' in error_lower or 'undefined' in error_lower:
            return 'unknown_keyword'
        elif '=' in code and '==' not in code and 'where' in code_lower:
            return 'wrong_operator'
        else:
            return 'other_parse_error'
    else:  # python
        if 'syntax' in error_lower:
            return 'syntax_error'
        elif 'indent' in error_lower:
            return 'indentation_error'
        elif 'name' in error_lower and 'not defined' in error_lower:
            return 'undefined_name'
        else:
            return 'other_parse_error'


def attempt_recovery(code: str, error_message: str, language: str) -> tuple[bool, str, str]:
    """
    Attempt to recover from parse errors using known fixes.
    Returns: (success, recovered_code, method)
    """
    if language != 'anka':
        return False, code, 'none'

    recovered = code
    methods = []

    # Recovery 1: Add missing INTO clause
    # Pattern: operation without INTO at end of line
    lines = recovered.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Check if line has operation but no INTO
        ops = ['FILTER', 'MAP', 'SELECT', 'SORT', 'LIMIT', 'SKIP', 'DISTINCT', 'AGGREGATE', 'JOIN', 'LEFT_JOIN']
        has_op = any(stripped.upper().startswith(op) or f' {op} ' in stripped.upper() for op in ops)
        has_into = 'INTO' in stripped.upper()

        if has_op and not has_into and stripped and not stripped.startswith('--'):
            # Try to add INTO with generated name
            var_name = f"result_{i}"
            new_lines.append(f"{line} INTO {var_name}")
            methods.append('add_into')
        else:
            new_lines.append(line)

    if 'add_into' in methods:
        recovered = '\n'.join(new_lines)

    # Recovery 2: Fix = to == in WHERE clauses
    if ' = ' in recovered and 'WHERE' in recovered.upper():
        # Be careful not to replace => or ==
        # Match = that's not part of == or =>
        recovered = re.sub(r'(?<![=!<>])=(?![=>])', '==', recovered)
        methods.append('fix_equals')

    # Recovery 3: Fix missing source in FILTER
    if re.search(r'FILTER\s+WHERE', recovered, re.IGNORECASE):
        # Try to find the input name from earlier in code
        input_match = re.search(r'INPUT\s+(\w+)\s*:', recovered, re.IGNORECASE)
        if input_match:
            input_name = input_match.group(1)
            recovered = re.sub(r'FILTER\s+WHERE', f'FILTER {input_name} WHERE', recovered, flags=re.IGNORECASE)
            methods.append('add_source')

    if methods:
        return True, recovered, '+'.join(methods)
    else:
        return False, code, 'none'


def compute_consistency(outputs: list) -> tuple[int, float]:
    """
    Compute consistency score for a list of outputs.
    Returns: (num_unique, consistency_score)
    """
    if not outputs:
        return 0, 0.0

    # Normalize outputs for comparison
    def normalize(out: Any) -> str:
        if out is None:
            return "NULL"
        return json.dumps(out, sort_keys=True)

    normalized = [normalize(o) for o in outputs]
    unique = set(normalized)
    num_unique = len(unique)

    # Consistency score: 1.0 if all same, decreases with more unique values
    # Score = 1 - (num_unique - 1) / num_samples
    consistency = 1.0 - (num_unique - 1) / len(outputs) if len(outputs) > 1 else 1.0

    return num_unique, max(0.0, consistency)


def compute_language_metrics(results: list[DetailedResult], language: str, model: str) -> LanguageMetrics:
    """Compute aggregated metrics for a language."""
    lang_results = [r for r in results if r.language == language and r.model == model]

    if not lang_results:
        return LanguageMetrics(language=language, model=model, total_samples=0, total_tasks=0)

    metrics = LanguageMetrics(
        language=language,
        model=model,
        total_samples=len(lang_results),
        total_tasks=len(set(r.task_id for r in lang_results))
    )

    # Count primary metrics
    metrics.overall_pass_count = sum(1 for r in lang_results if r.passed)
    metrics.overall_pass_rate = metrics.overall_pass_count / len(lang_results)

    # Parse success
    metrics.parse_success_count = sum(1 for r in lang_results if r.parse_success)
    metrics.parse_success_rate = metrics.parse_success_count / len(lang_results)

    # Recovery
    parse_failures = [r for r in lang_results if not r.parse_success]
    metrics.recovery_eligible_count = len(parse_failures)
    metrics.recovery_attempted_count = sum(1 for r in parse_failures if r.recovery_attempted)
    metrics.recovery_success_count = sum(1 for r in parse_failures if r.recovery_success)

    if metrics.recovery_eligible_count > 0:
        metrics.recovery_rate = metrics.recovery_success_count / metrics.recovery_eligible_count

    # Pass rate with recovery
    effective_passes = metrics.overall_pass_count + sum(1 for r in lang_results if r.passed_after_recovery)
    metrics.pass_rate_with_recovery = effective_passes / len(lang_results)

    # Execution success (of those that parsed)
    parsed = [r for r in lang_results if r.parse_success or r.recovery_success]
    if parsed:
        metrics.execution_success_rate = sum(1 for r in parsed if r.execution_success) / len(parsed)

    # Output correctness (of those that executed)
    executed = [r for r in lang_results if r.execution_success]
    if executed:
        metrics.output_correct_rate = sum(1 for r in executed if r.output_correct) / len(executed)

    # Error breakdown
    metrics.parse_error_count = sum(1 for r in lang_results if r.final_status == 'parse_error')
    metrics.runtime_error_count = sum(1 for r in lang_results if r.final_status == 'runtime_error')
    metrics.wrong_output_count = sum(1 for r in lang_results if r.final_status == 'wrong_output')

    # Consistency by task
    tasks = set(r.task_id for r in lang_results)
    consistency_scores = []
    fully_consistent = 0

    for task_id in tasks:
        task_results = [r for r in lang_results if r.task_id == task_id]
        outputs = [r.actual_output for r in task_results]
        num_unique, consistency = compute_consistency(outputs)
        consistency_scores.append(consistency)
        if num_unique == 1:
            fully_consistent += 1

    metrics.avg_consistency_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
    metrics.fully_consistent_tasks = fully_consistent

    # By category - extract category from task_id
    # Handle different task_id formats: "agg_001", "filter_001", etc.
    categories: dict[str, list[DetailedResult]] = {}
    for r in lang_results:
        # Extract category from task_id (everything before the underscore + number)
        parts = r.task_id.split('_')
        if len(parts) >= 2:
            cat = parts[0]
        else:
            cat = 'unknown'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)

    for cat, cat_results in categories.items():
        if cat_results:
            metrics.metrics_by_category[cat] = {
                'pass_rate': sum(1 for r in cat_results if r.passed) / len(cat_results),
                'parse_success_rate': sum(1 for r in cat_results if r.parse_success) / len(cat_results),
                'count': len(cat_results)
            }

    return metrics
