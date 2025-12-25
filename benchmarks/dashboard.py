"""Real-time optimization dashboard."""

import json
from pathlib import Path
from datetime import datetime


def show_dashboard():
    """Show optimization progress dashboard."""

    state_file = Path('benchmarks/optimization_state.json')
    if not state_file.exists():
        print("No optimization state found. Run benchmarks first.")
        return

    with open(state_file) as f:
        state = json.load(f)

    print("\n" + "="*70)
    print("  ANKA OPTIMIZATION DASHBOARD")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)

    # Overall progress
    tasks = state.get('tasks', {})
    total = len(tasks)
    fixed = sum(1 for t in tasks.values() if t.get('fixed', False))
    failing = sum(1 for t in tasks.values() if t.get('needs_attention', True))

    pct = fixed / total * 100 if total > 0 else 0
    bar_len = 40
    filled = int(bar_len * pct / 100)
    bar = '#' * filled + '-' * (bar_len - filled)

    print(f"\n  Progress: [{bar}] {pct:.1f}%")
    print(f"  Tasks: {fixed}/{total} fixed, {failing} need attention")

    # Iteration history
    iterations = state.get('iterations', [])
    if iterations:
        print(f"\n  Iteration History:")
        print(f"  {'#':<4} {'Model':<15} {'Anka':<10} {'Python':<10} {'Delta':<8}")
        print("  " + "-"*50)

        for it in iterations[-10:]:  # Last 10 iterations
            delta = it.get('improvement_from_last', 0)
            print(f"  {it['iteration']:<4} {it['model']:<15} "
                  f"{it['anka_pass_rate']*100:>6.1f}%   "
                  f"{it['python_pass_rate']*100:>6.1f}%   "
                  f"{delta*100:>+5.1f}%")

    # Best results by model
    best = state.get('best_results', {})
    if best:
        print(f"\n  Best Results by Model:")
        for model, results in best.items():
            print(f"    {model}: Anka {results.get('anka', 0)*100:.1f}%")

    # Categories needing work
    categories: dict = {}
    for tid, task in tasks.items():
        cat = task.get('category', tid.rsplit('_', 1)[0])
        if cat not in categories:
            categories[cat] = {'total': 0, 'fixed': 0}
        categories[cat]['total'] += 1
        if task.get('fixed', False):
            categories[cat]['fixed'] += 1

    print(f"\n  By Category:")
    for cat in sorted(categories.keys()):
        stats = categories[cat]
        cat_pct = stats['fixed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        status = "OK" if cat_pct >= 90 else "!!" if cat_pct >= 70 else "XX"
        print(f"    [{status}] {cat}: {stats['fixed']}/{stats['total']} ({cat_pct:.0f}%)")

    print("\n" + "="*70)


if __name__ == '__main__':
    show_dashboard()
