#!/usr/bin/env python3
"""Analyze partial benchmark results from both old and new runner formats."""

import json
from pathlib import Path
from collections import Counter
from typing import Any


def normalize_result(r: dict) -> dict:
    """Normalize result to common format (handles old and new runner formats)."""
    normalized = {
        'task_id': r.get('task_id', ''),
        'language': r.get('language', ''),
        'model': r.get('model', ''),
        'sample': r.get('sample', 1),
        'generated_code': r.get('generated_code', ''),
    }

    # Handle passed status (different field names in old vs new format)
    if 'passed' in r:
        normalized['passed'] = r['passed']
    elif 'output_correct' in r:
        normalized['passed'] = r['output_correct']
    elif 'pass_all' in r:
        normalized['passed'] = r['pass_all']
    else:
        normalized['passed'] = False

    # Handle parse success
    if 'parse_success' in r:
        normalized['parse_success'] = r['parse_success']
    else:
        # Old format: if there's an error, check if it's a parse error
        error = r.get('error', '')
        if error:
            normalized['parse_success'] = 'parse' not in str(error).lower() and 'syntax' not in str(error).lower()
        else:
            normalized['parse_success'] = True  # No error means it parsed

    # Handle final status
    if 'final_status' in r:
        normalized['final_status'] = r['final_status']
    elif normalized['passed']:
        normalized['final_status'] = 'pass'
    elif r.get('error'):
        error = str(r['error']).lower()
        if 'parse' in error or 'syntax' in error:
            normalized['final_status'] = 'parse_error'
        else:
            normalized['final_status'] = 'runtime_error'
    else:
        normalized['final_status'] = 'wrong_output'

    # Copy over other fields if present
    for key in ['parse_error', 'parse_error_type', 'execution_error', 'recovery_success', 'recovery_attempted', 'error']:
        if key in r:
            normalized[key] = r[key]

    return normalized


def analyze_partial_results(results_file: str | None = None) -> dict[str, Any]:
    """Analyze partial benchmark results.

    Args:
        results_file: Path to results file. If None, uses largest file with Anka results.

    Returns:
        The parsed results data.
    """
    results_dir = Path('benchmarks/results')

    if results_file:
        latest = Path(results_file)
    else:
        # Find the largest file with Anka results
        best_file = None
        best_anka_count = 0

        for f in results_dir.glob('run_*.json'):
            with open(f) as file:
                data = json.load(file)
            results = data.get('results', [])
            anka_count = sum(1 for r in results if r.get('language') == 'anka')
            if anka_count > best_anka_count:
                best_anka_count = anka_count
                best_file = f

        if not best_file:
            print("No results files found with Anka results!")
            return {}

        latest = best_file

    print(f"Analyzing: {latest}")
    print(f"File size: {latest.stat().st_size / 1024:.1f} KB")

    with open(latest) as f:
        data = json.load(f)

    # Normalize all results
    raw_results = data.get('results', [])
    results = [normalize_result(r) for r in raw_results]

    print(f"\nTotal samples recorded: {len(results)}")

    # Split by language
    anka_results = [r for r in results if r['language'] == 'anka']
    python_results = [r for r in results if r['language'] == 'python']

    print(f"Anka samples: {len(anka_results)}")
    print(f"Python samples: {len(python_results)}")

    # Tasks completed
    anka_tasks = set(r['task_id'] for r in anka_results)
    python_tasks = set(r['task_id'] for r in python_results)
    print(f"\nAnka tasks: {len(anka_tasks)}")
    print(f"Python tasks: {len(python_tasks)}")

    print("\n" + "=" * 70)
    print("ANKA METRICS")
    print("=" * 70)

    if anka_results:
        # Parse success
        parse_success = sum(1 for r in anka_results if r.get('parse_success', False))
        print(f"Parse Success: {parse_success}/{len(anka_results)} ({parse_success / len(anka_results) * 100:.1f}%)")

        # Recovery
        parse_failures = [r for r in anka_results if not r.get('parse_success', False)]
        recovery_success = sum(1 for r in parse_failures if r.get('recovery_success', False))
        if parse_failures:
            print(f"Recovery: {recovery_success}/{len(parse_failures)} parse failures recovered ({recovery_success / len(parse_failures) * 100:.1f}%)")

        # Overall pass
        passed = sum(1 for r in anka_results if r.get('passed', False))
        print(f"Overall Pass: {passed}/{len(anka_results)} ({passed / len(anka_results) * 100:.1f}%)")

        # Error breakdown
        statuses = Counter(r.get('final_status', 'unknown') for r in anka_results)
        print(f"\nError Breakdown:")
        for status, count in statuses.most_common():
            print(f"  {status}: {count} ({count / len(anka_results) * 100:.1f}%)")

        # Parse error types
        parse_errors = [r for r in anka_results if r.get('parse_error_type')]
        if parse_errors:
            error_types = Counter(r['parse_error_type'] for r in parse_errors)
            print(f"\nParse Error Types:")
            for err_type, count in error_types.most_common():
                print(f"  {err_type}: {count}")

    print("\n" + "=" * 70)
    print("PYTHON METRICS")
    print("=" * 70)

    if python_results:
        # Parse success
        parse_success = sum(1 for r in python_results if r.get('parse_success', False))
        print(f"Parse Success: {parse_success}/{len(python_results)} ({parse_success / len(python_results) * 100:.1f}%)")

        # Overall pass
        passed = sum(1 for r in python_results if r.get('passed', False))
        print(f"Overall Pass: {passed}/{len(python_results)} ({passed / len(python_results) * 100:.1f}%)")

        # Error breakdown
        statuses = Counter(r.get('final_status', 'unknown') for r in python_results)
        print(f"\nError Breakdown:")
        for status, count in statuses.most_common():
            print(f"  {status}: {count} ({count / len(python_results) * 100:.1f}%)")

    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)

    if anka_results and python_results:
        anka_pass = sum(1 for r in anka_results if r.get('passed', False)) / len(anka_results)
        python_pass = sum(1 for r in python_results if r.get('passed', False)) / len(python_results)

        anka_parse = sum(1 for r in anka_results if r.get('parse_success', False)) / len(anka_results)
        python_parse = sum(1 for r in python_results if r.get('parse_success', False)) / len(python_results)

        print(f"\n{'Metric':<25} {'Anka':<15} {'Python':<15} {'Diff':<10}")
        print("-" * 65)
        print(f"{'Parse Success Rate':<25} {anka_parse * 100:>6.1f}%        {python_parse * 100:>6.1f}%        {(anka_parse - python_parse) * 100:>+6.1f}%")
        print(f"{'Overall Pass Rate':<25} {anka_pass * 100:>6.1f}%        {python_pass * 100:>6.1f}%        {(anka_pass - python_pass) * 100:>+6.1f}%")

    # By category
    print("\n" + "=" * 70)
    print("BY CATEGORY")
    print("=" * 70)

    categories: set[str] = set()
    for r in results:
        task_id = r.get('task_id', '')
        parts = task_id.split('_')
        if len(parts) >= 2:
            cat = parts[0]
        else:
            cat = task_id
        categories.add(cat)

    print(f"\n{'Category':<20} {'Anka Pass%':<15} {'Python Pass%':<15} {'Samples':<10}")
    print("-" * 60)

    for cat in sorted(categories):
        cat_anka = [r for r in anka_results if r['task_id'].startswith(cat + '_')]
        cat_python = [r for r in python_results if r['task_id'].startswith(cat + '_')]

        if cat_anka:
            anka_rate = sum(1 for r in cat_anka if r.get('passed', False)) / len(cat_anka)
        else:
            anka_rate = 0

        if cat_python:
            python_rate = sum(1 for r in cat_python if r.get('passed', False)) / len(cat_python)
        else:
            python_rate = 0

        samples = len(cat_anka) + len(cat_python)
        print(f"{cat:<20} {anka_rate * 100:>6.1f}%        {python_rate * 100:>6.1f}%        {samples}")

    # Sample some failures
    print("\n" + "=" * 70)
    print("SAMPLE ANKA FAILURES (for prompt improvement)")
    print("=" * 70)

    anka_failures = [r for r in anka_results if not r.get('passed', False)]

    for i, failure in enumerate(anka_failures[:5]):
        print(f"\n--- Failure {i + 1}: {failure['task_id']} ---")
        print(f"Status: {failure.get('final_status', 'unknown')}")
        print(f"Parse Error Type: {failure.get('parse_error_type', 'N/A')}")
        error_msg = str(failure.get('parse_error') or failure.get('execution_error') or failure.get('error') or 'N/A')
        print(f"Error: {error_msg[:200]}")
        print(f"Code (first 300 chars):")
        print(failure.get('generated_code', 'N/A')[:300])

    # Last task info
    print("\n" + "=" * 70)
    print("LAST COMPLETED TASK")
    print("=" * 70)

    if results:
        last = results[-1]
        sample_info = f"sample {last.get('sample', 'N/A')}"
        print(f"Last completed: {last['task_id']} | {last['language']} | {sample_info}")
        print(f"Status: {last.get('final_status', 'unknown')}")

    return data


def analyze_all_results() -> None:
    """Analyze all results files and summarize."""
    results_dir = Path('benchmarks/results')

    print("=" * 70)
    print("ALL BENCHMARK RESULTS SUMMARY")
    print("=" * 70)

    total_anka_pass = 0
    total_anka_count = 0
    total_python_pass = 0
    total_python_count = 0

    for f in sorted(results_dir.glob('run_*.json')):
        with open(f) as file:
            data = json.load(file)

        raw_results = data.get('results', [])
        if not raw_results:
            continue

        results = [normalize_result(r) for r in raw_results]

        anka = [r for r in results if r['language'] == 'anka']
        python = [r for r in results if r['language'] == 'python']

        if not anka:  # Skip files without Anka results
            continue

        anka_pass = sum(1 for r in anka if r.get('passed', False))
        python_pass = sum(1 for r in python if r.get('passed', False))

        total_anka_pass += anka_pass
        total_anka_count += len(anka)
        total_python_pass += python_pass
        total_python_count += len(python)

        anka_rate = anka_pass / len(anka) * 100 if anka else 0
        python_rate = python_pass / len(python) * 100 if python else 0

        print(f"{f.name}: Anka {anka_rate:>5.1f}% ({anka_pass}/{len(anka)}), Python {python_rate:>5.1f}% ({python_pass}/{len(python)})")

    print("\n" + "-" * 70)
    if total_anka_count:
        print(f"TOTAL Anka: {total_anka_pass / total_anka_count * 100:.1f}% ({total_anka_pass}/{total_anka_count})")
    if total_python_count:
        print(f"TOTAL Python: {total_python_pass / total_python_count * 100:.1f}% ({total_python_pass}/{total_python_count})")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            analyze_all_results()
        else:
            analyze_partial_results(sys.argv[1])
    else:
        analyze_partial_results()
