#!/usr/bin/env python3
"""Analyze Anka failures to identify optimization opportunities."""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any


def analyze_failures(results_file: str = 'benchmarks/results/run_a6812fbb.json') -> dict[str, list]:
    """Analyze all Anka failures and categorize them."""

    with open(results_file) as f:
        data = json.load(f)

    results = data['results']
    anka_results = [r for r in results if r['language'] == 'anka']
    python_results = [r for r in results if r['language'] == 'python']

    # Build Python pass rates by task for comparison
    python_by_task: dict[str, list] = defaultdict(list)
    for r in python_results:
        python_by_task[r['task_id']].append(r)

    # Helper to check if result passed (handles both old and new format)
    def is_passed(r: dict) -> bool:
        return r.get('passed', False) or r.get('output_correct', False) or r.get('pass_all', False)

    # Group failures by task
    failures_by_task: dict[str, list] = defaultdict(list)
    for r in anka_results:
        if not is_passed(r):
            failures_by_task[r['task_id']].append(r)

    print("=" * 80)
    print("ANKA FAILURES BY TASK")
    print("=" * 80)

    # Sort by number of failures (most failures first)
    sorted_tasks = sorted(failures_by_task.items(), key=lambda x: -len(x[1]))

    for task_id, failures in sorted_tasks:
        fail_count = len(failures)
        status_counts: dict[str, int] = defaultdict(int)
        for f in failures:
            status = f.get('final_status', 'unknown')
            if status == 'unknown':
                # Try to infer from old format
                error = f.get('error', '')
                if error:
                    if 'parse' in str(error).lower() or 'syntax' in str(error).lower():
                        status = 'parse_error'
                    else:
                        status = 'runtime_error'
                else:
                    status = 'wrong_output'
            status_counts[status] += 1

        # Get Python pass rate for comparison
        py_results = python_by_task.get(task_id, [])
        py_pass = sum(1 for r in py_results if is_passed(r))
        py_rate = py_pass / len(py_results) * 100 if py_results else 0

        print(f"\n{'=' * 60}")
        print(f"TASK: {task_id} | Anka Failures: {fail_count}/10 | Python: {py_rate:.0f}%")
        print(f"{'=' * 60}")
        print(f"Error types: {dict(status_counts)}")

        # Show first failure details
        f = failures[0]
        print(f"\nGenerated Code:")
        print("-" * 40)
        code = f.get('generated_code', 'N/A')
        print(code[:800] if code else 'N/A')

        if f.get('parse_error'):
            print(f"\nParse Error: {f['parse_error'][:300]}")

        if f.get('execution_error') or f.get('error'):
            error = f.get('execution_error') or f.get('error')
            print(f"\nExecution Error: {str(error)[:300]}")

        if f.get('actual_output') is not None:
            print(f"\nActual Output: {json.dumps(f['actual_output'], indent=2)[:500]}")

        if f.get('expected_output') is not None:
            print(f"\nExpected Output: {json.dumps(f['expected_output'], indent=2)[:500]}")

    # Summary by category
    print("\n" + "=" * 80)
    print("FAILURE SUMMARY BY CATEGORY")
    print("=" * 80)

    categories: dict[str, dict[str, int]] = defaultdict(lambda: {'total': 0, 'failed': 0})
    for r in anka_results:
        # Extract category from task_id (e.g., filter_001 -> filter)
        parts = r['task_id'].rsplit('_', 1)
        cat = parts[0] if len(parts) > 1 else r['task_id']
        categories[cat]['total'] += 1
        if not is_passed(r):
            categories[cat]['failed'] += 1

    print(f"\n{'Category':<15} {'Pass Rate':<12} {'Failures':<10}")
    print("-" * 40)
    for cat in sorted(categories.keys()):
        stats = categories[cat]
        pass_rate = (stats['total'] - stats['failed']) / stats['total'] * 100
        print(f"{cat:<15} {pass_rate:>6.1f}%      {stats['failed']}/{stats['total']}")

    return failures_by_task


def categorize_failures(results_file: str = 'benchmarks/results/run_a6812fbb.json') -> dict[str, list]:
    """Categorize all failures by type for targeted fixes."""

    with open(results_file) as f:
        data = json.load(f)

    results = data['results']

    # Helper to check if result passed
    def is_passed(r: dict) -> bool:
        return r.get('passed', False) or r.get('output_correct', False) or r.get('pass_all', False)

    categories: dict[str, list] = {
        'task_bugs': [],      # Both languages fail → task definition wrong
        'prompt_issues': [],  # Only Anka fails → prompt needs improvement
        'grammar_gaps': [],   # Parse errors → grammar needs aliases
        'runtime_bugs': [],   # Execution errors → interpreter bugs
    }

    # Group by task
    by_task: dict[str, dict[str, list]] = defaultdict(lambda: {'anka': [], 'python': []})
    for r in results:
        by_task[r['task_id']][r['language']].append(r)

    for task_id, langs in by_task.items():
        anka_results = langs['anka']
        python_results = langs['python']

        anka_pass_rate = sum(1 for r in anka_results if is_passed(r)) / len(anka_results) if anka_results else 0
        python_pass_rate = sum(1 for r in python_results if is_passed(r)) / len(python_results) if python_results else 0

        anka_failures = [r for r in anka_results if not is_passed(r)]

        if not anka_failures:
            continue

        # Categorize based on failure type
        sample = anka_failures[0]
        status = sample.get('final_status', 'unknown')

        # Infer status from old format if needed
        if status == 'unknown':
            error = sample.get('error', '')
            if error:
                if 'parse' in str(error).lower() or 'syntax' in str(error).lower():
                    status = 'parse_error'
                else:
                    status = 'runtime_error'
            else:
                status = 'wrong_output'

        if anka_pass_rate < 0.5 and python_pass_rate < 0.5:
            # Both languages fail → task bug
            categories['task_bugs'].append({
                'task_id': task_id,
                'anka_rate': anka_pass_rate,
                'python_rate': python_pass_rate,
                'sample_error': sample.get('execution_error') or sample.get('parse_error') or sample.get('error'),
                'sample_output': sample.get('actual_output'),
                'expected_output': sample.get('expected_output'),
            })
        elif status == 'parse_error':
            categories['grammar_gaps'].append({
                'task_id': task_id,
                'error': sample.get('parse_error') or sample.get('error'),
                'code': sample.get('generated_code', '')[:500],
            })
        elif status == 'runtime_error':
            categories['runtime_bugs'].append({
                'task_id': task_id,
                'error': sample.get('execution_error') or sample.get('error'),
                'code': sample.get('generated_code', '')[:500],
            })
        else:
            # Only Anka fails with wrong output → prompt issue
            categories['prompt_issues'].append({
                'task_id': task_id,
                'anka_rate': anka_pass_rate,
                'python_rate': python_pass_rate,
                'actual': sample.get('actual_output'),
                'expected': sample.get('expected_output'),
                'code': sample.get('generated_code', '')[:500],
            })

    return categories


def generate_fix_report(categories: dict[str, list]) -> None:
    """Generate report with specific fixes needed."""

    print("\n" + "=" * 80)
    print("ANKA OPTIMIZATION REPORT")
    print("=" * 80)

    print(f"\n## Summary")
    print(f"- Task Definition Bugs: {len(categories['task_bugs'])} tasks")
    print(f"- Prompt Issues: {len(categories['prompt_issues'])} tasks")
    print(f"- Grammar Gaps: {len(categories['grammar_gaps'])} tasks")
    print(f"- Runtime Bugs: {len(categories['runtime_bugs'])} tasks")

    if categories['task_bugs']:
        print(f"\n{'=' * 60}")
        print("TASK DEFINITION BUGS (both languages fail)")
        print("Fix: Update task JSON expected outputs")
        print(f"{'=' * 60}")
        for item in categories['task_bugs']:
            print(f"\n  {item['task_id']}: Anka {item['anka_rate']*100:.0f}%, Python {item['python_rate']*100:.0f}%")
            if item.get('sample_error'):
                print(f"    Error: {str(item['sample_error'])[:100]}")
            if item.get('expected_output'):
                print(f"    Expected: {str(item['expected_output'])[:100]}")
            if item.get('sample_output'):
                print(f"    Actual: {str(item['sample_output'])[:100]}")

    if categories['prompt_issues']:
        print(f"\n{'=' * 60}")
        print("PROMPT ISSUES (Anka fails, Python succeeds)")
        print("Fix: Add examples to anka_prompt.md or fix task definitions")
        print(f"{'=' * 60}")
        for item in categories['prompt_issues']:
            print(f"\n  {item['task_id']}: Anka {item['anka_rate']*100:.0f}%, Python {item['python_rate']*100:.0f}%")
            print(f"    Expected: {str(item.get('expected'))[:100]}")
            print(f"    Actual: {str(item.get('actual'))[:100]}")

    if categories['grammar_gaps']:
        print(f"\n{'=' * 60}")
        print("GRAMMAR GAPS (parse errors)")
        print("Fix: Add grammar aliases or features")
        print(f"{'=' * 60}")
        for item in categories['grammar_gaps']:
            print(f"\n  {item['task_id']}")
            print(f"    Error: {str(item.get('error', 'N/A'))[:150]}")

    if categories['runtime_bugs']:
        print(f"\n{'=' * 60}")
        print("RUNTIME BUGS (execution errors)")
        print("Fix: Fix Anka interpreter")
        print(f"{'=' * 60}")
        for item in categories['runtime_bugs']:
            print(f"\n  {item['task_id']}")
            print(f"    Error: {str(item.get('error', 'N/A'))[:150]}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
    else:
        results_file = 'benchmarks/results/run_a6812fbb.json'

    print(f"Using results: {results_file}")

    print("\nAnalyzing failures...")
    analyze_failures(results_file)

    print("\n\nCategorizing failures...")
    categories = categorize_failures(results_file)

    generate_fix_report(categories)

    # Save detailed report
    report_dir = Path('benchmarks/reports')
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / 'optimization_report.json'
    with open(report_file, 'w') as f:
        json.dump(categories, f, indent=2, default=str)
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == '__main__':
    main()
