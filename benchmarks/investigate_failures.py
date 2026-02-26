"""
Investigate specific failing tasks in detail.
"""

import json
from pathlib import Path
from typing import Optional

from benchmarks.optimization_tracker import OptimizationState


def find_task_file(task_id: str) -> Optional[Path]:
    """Find the task definition file for a given task ID."""
    tasks_dir = Path('benchmarks/tasks')

    for category_dir in tasks_dir.iterdir():
        if category_dir.is_dir():
            for task_file in category_dir.glob('*.json'):
                with open(task_file) as f:
                    task = json.load(f)
                if task.get('id') == task_id:
                    return task_file

    return None


def investigate_task(task_id: str) -> None:
    """Deep dive into a specific failing task."""

    # Load task definition
    task_file = find_task_file(task_id)

    if not task_file:
        print(f"Task {task_id} not found!")
        return

    with open(task_file) as f:
        task = json.load(f)

    print(f"\n{'='*70}")
    print(f"INVESTIGATING: {task_id}")
    print(f"{'='*70}")
    print(f"File: {task_file}")
    print(f"Category: {task.get('category', 'unknown')}")
    print(f"Difficulty: {task.get('difficulty', 'easy')}")
    print(f"Domain: {task.get('domain', 'general')}")

    print(f"\nPROMPT/DESCRIPTION:")
    print(task.get('prompt') or task.get('description', 'N/A'))

    print(f"\nINPUT SCHEMA:")
    print(json.dumps(task.get('input_schema', {}), indent=2))

    print(f"\nTEST CASES:")
    for i, tc in enumerate(task.get('test_cases', [])):
        print(f"\n  Test {i+1}:")
        input_str = json.dumps(tc.get('input', {}))
        if len(input_str) > 200:
            input_str = input_str[:200] + "..."
        print(f"    Input: {input_str}")

        expected = tc.get('expected') if 'expected' in tc else tc.get('expected_output')
        expected_str = json.dumps(expected)
        if len(expected_str) > 200:
            expected_str = expected_str[:200] + "..."
        print(f"    Expected: {expected_str}")

    # Load results to see what LLM produced
    state = OptimizationState.load()
    if task_id in state.tasks:
        task_state = state.tasks[task_id]
        print(f"\nRESULTS:")
        for model, results in task_state.results.items():
            print(f"  {model}: Anka {results.get('anka', 0)*100:.0f}%, Python {results.get('python', 0)*100:.0f}%")

        if task_state.common_errors:
            print(f"\nCOMMON ERRORS:")
            for err in task_state.common_errors[:3]:
                print(f"  - {err[:100]}")

    # Check the actual results file for generated code
    results_dir = Path('benchmarks/results')
    result_files = sorted(results_dir.glob('run_*.json'), key=lambda p: p.stat().st_mtime)

    if result_files:
        with open(result_files[-1]) as f:
            results_data = json.load(f)

        task_results = [r for r in results_data.get('results', []) if r.get('task_id') == task_id]

        if task_results:
            print(f"\nGENERATED CODE SAMPLES:")

            for lang in ['anka', 'python']:
                lang_results = [r for r in task_results if r.get('language') == lang]
                if lang_results:
                    sample = lang_results[0]
                    passed = sample.get('passed') or sample.get('output_correct')
                    status = "PASS" if passed else "FAIL"
                    print(f"\n  {lang.upper()} ({status}):")

                    code = sample.get('generated_code', 'N/A')
                    if len(code) > 500:
                        code = code[:500] + "\n    ... (truncated)"
                    print(f"    Code:\n{code}")

                    if sample.get('actual_output') is not None:
                        actual_str = json.dumps(sample.get('actual_output'))
                        if len(actual_str) > 200:
                            actual_str = actual_str[:200] + "..."
                        print(f"\n    Actual output: {actual_str}")

                    if sample.get('execution_error'):
                        err = sample.get('execution_error')
                        if len(err) > 200:
                            err = err[:200] + "..."
                        print(f"\n    Error: {err}")

                    if sample.get('parse_error'):
                        err = sample.get('parse_error')
                        if len(err) > 200:
                            err = err[:200] + "..."
                        print(f"\n    Parse Error: {err}")


def investigate_all_bugs() -> None:
    """Investigate all task bugs (where both languages fail)."""
    state = OptimizationState.load()

    bugs = []
    for tid, task in state.tasks.items():
        for model in task.results:
            if task.anka_pass_rate(model) < 0.5 and task.python_pass_rate(model) < 0.5:
                bugs.append(tid)
                break

    print(f"Found {len(bugs)} task bugs to investigate\n")

    for tid in bugs:
        investigate_task(tid)
        print("\n" + "-"*70 + "\n")


def investigate_anka_failures() -> None:
    """Investigate tasks where Anka fails but Python passes."""
    state = OptimizationState.load()

    failures = []
    for tid, task in state.tasks.items():
        for model in task.results:
            anka_rate = task.anka_pass_rate(model)
            python_rate = task.python_pass_rate(model)
            if anka_rate < 0.5 and python_rate >= 0.5:
                failures.append((tid, anka_rate, python_rate))
                break

    print(f"Found {len(failures)} Anka-only failures to investigate\n")

    for tid, anka, python in failures:
        print(f"\n{tid}: Anka {anka*100:.0f}% vs Python {python*100:.0f}%")
        investigate_task(tid)
        print("\n" + "-"*70 + "\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--bugs':
            investigate_all_bugs()
        elif sys.argv[1] == '--anka':
            investigate_anka_failures()
        else:
            investigate_task(sys.argv[1])
    else:
        print("Usage:")
        print("  python benchmarks/investigate_failures.py <task_id>  # Investigate specific task")
        print("  python benchmarks/investigate_failures.py --bugs     # Investigate all task bugs")
        print("  python benchmarks/investigate_failures.py --anka     # Investigate Anka-only failures")
