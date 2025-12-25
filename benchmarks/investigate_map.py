"""Investigate MAP task failures."""

import json
from pathlib import Path


def investigate_map():
    """Find why Anka is losing on map tasks."""

    # Load latest results
    results_dir = Path('benchmarks/results')
    result_files = sorted(results_dir.glob('run_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not result_files:
        print("No results found!")
        return

    with open(result_files[0]) as f:
        data = json.load(f)

    results = data.get('results', [])

    # Find map task failures
    map_results = [r for r in results if r.get('task_id', '').startswith('map_')]

    anka_map = [r for r in map_results if r.get('language') == 'anka']
    python_map = [r for r in map_results if r.get('language') == 'python']

    print("="*70)
    print("MAP TASK ANALYSIS")
    print("="*70)

    # Group by task
    by_task = {}
    for r in map_results:
        tid = r.get('task_id')
        if tid not in by_task:
            by_task[tid] = {'anka': [], 'python': []}
        by_task[tid][r.get('language')].append(r)

    print(f"\n{'Task':<12} {'Anka':<10} {'Python':<10} {'Issue':<30}")
    print("-"*65)

    for tid in sorted(by_task.keys()):
        anka_results = by_task[tid]['anka']
        python_results = by_task[tid]['python']

        anka_pass = sum(1 for r in anka_results if r.get('passed') or r.get('output_correct', False))
        python_pass = sum(1 for r in python_results if r.get('passed') or r.get('output_correct', False))

        anka_rate = f"{anka_pass}/{len(anka_results)}"
        python_rate = f"{python_pass}/{len(python_results)}"

        # Determine issue
        if anka_pass < python_pass:
            issue = "ANKA LOSING"
        elif anka_pass > python_pass:
            issue = "Anka winning"
        else:
            issue = "Tied"

        print(f"{tid:<12} {anka_rate:<10} {python_rate:<10} {issue:<30}")

    # Deep dive into Anka failures
    print("\n" + "="*70)
    print("ANKA MAP FAILURES - DETAILED")
    print("="*70)

    anka_failures = [r for r in anka_map if not (r.get('passed') or r.get('output_correct', False))]

    for r in anka_failures[:5]:
        print(f"\n{'-'*50}")
        print(f"Task: {r.get('task_id')}")
        print(f"Status: {r.get('final_status', 'unknown')}")

        if r.get('parse_error'):
            print(f"Parse Error: {r.get('parse_error')[:200]}")

        if r.get('execution_error'):
            print(f"Execution Error: {r.get('execution_error')[:200]}")

        print(f"\nGenerated Code:")
        print(r.get('generated_code', 'N/A')[:500])

        if r.get('actual_output') is not None:
            print(f"\nActual Output: {json.dumps(r.get('actual_output'))[:200]}")

        if r.get('expected_output') is not None:
            print(f"Expected Output: {json.dumps(r.get('expected_output'))[:200]}")


if __name__ == '__main__':
    investigate_map()
