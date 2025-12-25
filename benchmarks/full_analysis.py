"""
Comprehensive optimization analysis for Anka benchmarks.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any

from benchmarks.optimization_tracker import OptimizationState


def load_task_metadata() -> Dict[str, Dict[str, str]]:
    """Load task metadata from task files."""
    tasks_dir = Path('benchmarks/tasks')
    metadata = {}

    for category_dir in tasks_dir.iterdir():
        if category_dir.is_dir():
            for task_file in category_dir.glob('*.json'):
                with open(task_file) as f:
                    task = json.load(f)
                metadata[task['id']] = {
                    'difficulty': task.get('difficulty', 'easy'),
                    'domain': task.get('domain', 'general'),
                    'category': task.get('category', category_dir.name)
                }

    return metadata


def full_analysis() -> Dict[str, List]:
    """Run comprehensive analysis on benchmark results."""
    state = OptimizationState.load()
    task_metadata = load_task_metadata()

    print("="*80)
    print("COMPREHENSIVE OPTIMIZATION ANALYSIS")
    print("="*80)

    # Overall stats
    total_tasks = len(state.tasks)
    fixed = sum(1 for t in state.tasks.values() if t.fixed)
    failing = sum(1 for t in state.tasks.values() if t.needs_attention)

    print(f"\nOVERALL: {fixed}/{total_tasks} tasks passing ({fixed/total_tasks*100:.1f}%)")
    print(f"Failing: {failing} tasks need attention")

    # By category
    print("\n" + "="*80)
    print("BY CATEGORY")
    print("="*80)

    by_category: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'total': 0, 'fixed': 0, 'anka_rates': [], 'python_rates': []})

    for tid, task in state.tasks.items():
        cat = task.category
        by_category[cat]['total'] += 1
        if task.fixed:
            by_category[cat]['fixed'] += 1

        for model, results in task.results.items():
            by_category[cat]['anka_rates'].append(results.get('anka', 0))
            by_category[cat]['python_rates'].append(results.get('python', 0))

    print(f"\n{'Category':<15} {'Pass':<10} {'Anka Avg':<12} {'Python Avg':<12} {'Delta':<8}")
    print("-"*60)

    for cat in sorted(by_category.keys()):
        stats = by_category[cat]
        pct = stats['fixed'] / stats['total'] * 100 if stats['total'] > 0 else 0

        anka_avg = sum(stats['anka_rates']) / len(stats['anka_rates']) if stats['anka_rates'] else 0
        python_avg = sum(stats['python_rates']) / len(stats['python_rates']) if stats['python_rates'] else 0
        diff = anka_avg - python_avg

        status = "OK" if pct >= 90 else "!!" if pct >= 70 else "XX"
        print(f"[{status}] {cat:<11} {stats['fixed']}/{stats['total']:<6} {anka_avg*100:>6.1f}%      {python_avg*100:>6.1f}%      {diff*100:>+5.1f}%")

    # By difficulty
    print("\n" + "="*80)
    print("BY DIFFICULTY")
    print("="*80)

    by_diff: Dict[str, Dict[str, List]] = defaultdict(lambda: {'anka': [], 'python': []})

    for tid, task in state.tasks.items():
        # Get difficulty from metadata
        diff = task_metadata.get(tid, {}).get('difficulty', 'easy')

        # Override for hard category
        if task.category == 'hard':
            diff = 'hard'

        for model, results in task.results.items():
            by_diff[diff]['anka'].append(results.get('anka', 0))
            by_diff[diff]['python'].append(results.get('python', 0))

    print(f"\n{'Difficulty':<12} {'Tasks':<8} {'Anka':<12} {'Python':<12} {'Advantage':<12}")
    print("-"*55)

    for diff in ['easy', 'medium', 'hard']:
        anka = by_diff[diff]['anka']
        python = by_diff[diff]['python']

        if not anka:
            continue

        anka_avg = sum(anka) / len(anka)
        python_avg = sum(python) / len(python) if python else 0
        advantage = anka_avg - python_avg

        print(f"{diff:<12} {len(anka):<8} {anka_avg*100:>6.1f}%      {python_avg*100:>6.1f}%      {advantage*100:>+6.1f}%")

    # By domain
    print("\n" + "="*80)
    print("BY DOMAIN")
    print("="*80)

    by_domain: Dict[str, Dict[str, List]] = defaultdict(lambda: {'anka': [], 'python': []})

    for tid, task in state.tasks.items():
        domain = task_metadata.get(tid, {}).get('domain', 'general')

        for model, results in task.results.items():
            by_domain[domain]['anka'].append(results.get('anka', 0))
            by_domain[domain]['python'].append(results.get('python', 0))

    print(f"\n{'Domain':<15} {'Tasks':<8} {'Anka':<12} {'Python':<12} {'Advantage':<12}")
    print("-"*60)

    for domain in sorted(by_domain.keys()):
        anka = by_domain[domain]['anka']
        python = by_domain[domain]['python']

        if not anka:
            continue

        anka_avg = sum(anka) / len(anka)
        python_avg = sum(python) / len(python) if python else 0
        advantage = anka_avg - python_avg

        print(f"{domain:<15} {len(anka):<8} {anka_avg*100:>6.1f}%      {python_avg*100:>6.1f}%      {advantage*100:>+6.1f}%")

    # Failure Analysis
    print("\n" + "="*80)
    print("FAILURE ANALYSIS")
    print("="*80)

    task_bugs: List[Tuple] = []  # Both languages fail
    anka_only_fail: List[Tuple] = []  # Anka fails, Python passes
    python_only_fail: List[Tuple] = []  # Python fails, Anka passes

    for tid, task in state.tasks.items():
        if not task.needs_attention and not any(task.python_pass_rate(m) < 0.9 for m in task.results):
            continue

        for model in task.results:
            anka_rate = task.anka_pass_rate(model)
            python_rate = task.python_pass_rate(model)

            if anka_rate < 0.5 and python_rate < 0.5:
                task_bugs.append((tid, anka_rate, python_rate, task.common_errors))
            elif anka_rate < 0.5 and python_rate >= 0.5:
                anka_only_fail.append((tid, anka_rate, python_rate, task.common_errors))
            elif python_rate < 0.5 and anka_rate >= 0.5:
                python_only_fail.append((tid, anka_rate, python_rate, task.common_errors))
            break  # Only count once per task

    print(f"\n1. TASK BUGS (both languages fail): {len(task_bugs)}")
    print("   These are likely task definition issues - fix the JSON")
    for tid, anka, python, errors in task_bugs[:10]:
        print(f"   - {tid}: Anka {anka*100:.0f}%, Python {python*100:.0f}%")
        if errors:
            print(f"     Error: {errors[0][:60]}...")
    if len(task_bugs) > 10:
        print(f"   ... and {len(task_bugs) - 10} more")

    print(f"\n2. ANKA-ONLY FAILURES (Python passes): {len(anka_only_fail)}")
    print("   These need prompt improvements or grammar fixes")
    for tid, anka, python, errors in anka_only_fail[:10]:
        print(f"   - {tid}: Anka {anka*100:.0f}%, Python {python*100:.0f}%")
        if errors:
            print(f"     Error: {errors[0][:60]}...")
    if len(anka_only_fail) > 10:
        print(f"   ... and {len(anka_only_fail) - 10} more")

    print(f"\n3. PYTHON-ONLY FAILURES (Anka passes): {len(python_only_fail)}")
    print("   These show Anka's advantage!")
    for tid, anka, python, errors in python_only_fail[:10]:
        print(f"   - {tid}: Anka {anka*100:.0f}%, Python {python*100:.0f}%")

    # Priority fixes
    print("\n" + "="*80)
    print("PRIORITY FIXES")
    print("="*80)

    print("\nHIGH PRIORITY (fix these first):")

    # Task bugs in important categories
    important_cats = ['fin', 'hard', 'agg', 'multi']
    high_priority = [t for t in task_bugs if any(c in t[0] for c in important_cats)]
    for tid, anka, python, errors in high_priority[:5]:
        print(f"  - {tid}: Task definition bug")

    # Anka failures in finance (important for paper)
    finance_failures = [t for t in anka_only_fail if 'fin' in t[0]]
    for tid, anka, python, errors in finance_failures[:5]:
        print(f"  - {tid}: Anka prompt needs finance examples")

    print("\nMEDIUM PRIORITY:")
    other_anka_failures = [t for t in anka_only_fail if 'fin' not in t[0]][:5]
    for tid, anka, python, errors in other_anka_failures:
        print(f"  - {tid}: Improve Anka prompt")

    # Generate fix commands
    print("\n" + "="*80)
    print("RECOMMENDED ACTIONS")
    print("="*80)

    if task_bugs:
        print(f"\n1. Fix {len(task_bugs)} task definition bugs:")
        print("   Review and update these task JSON files to fix expected outputs")
        bug_cats = set(t[0].rsplit('_', 1)[0] for t in task_bugs)
        for cat in bug_cats:
            count = sum(1 for t in task_bugs if t[0].startswith(cat))
            print(f"   - benchmarks/tasks/{cat}/ ({count} bugs)")

    if anka_only_fail:
        print(f"\n2. Improve Anka prompt for {len(anka_only_fail)} failing tasks:")
        print("   Add more examples to benchmarks/prompts/anka_prompt.md")
        fail_cats = set(t[0].rsplit('_', 1)[0] for t in anka_only_fail)
        print(f"   Categories needing examples: {', '.join(sorted(fail_cats))}")

    print("\n3. After fixes, re-run focused test:")
    print("   python -m benchmarks.smart_runner focus --model haiku --samples 3")

    print("\n4. When all categories >85%, run full benchmark:")
    print("   python -m benchmarks.smart_runner full --model haiku --samples 10")

    return {
        'task_bugs': task_bugs,
        'anka_only_fail': anka_only_fail,
        'python_only_fail': python_only_fail
    }


if __name__ == '__main__':
    full_analysis()
