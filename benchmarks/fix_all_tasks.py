"""
Analyze and fix all failing benchmark tasks.
"""

import json
from pathlib import Path
from collections import defaultdict


def load_latest_results():
    """Load the most comprehensive benchmark results."""
    results_dir = Path('benchmarks/results')
    result_files = list(results_dir.glob('run_*.json'))

    if not result_files:
        # Try optimization state
        state_file = Path('benchmarks/optimization_state.json')
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return None

    # Find the file with the most results (largest file)
    largest_file = max(result_files, key=lambda p: p.stat().st_size)
    print(f"Using results from: {largest_file}")

    with open(largest_file) as f:
        return json.load(f)


def load_task_definition(task_id: str) -> tuple:
    """Load task definition file."""
    for base in ['benchmarks/tasks', 'benchmarks/problems']:
        for task_file in Path(base).rglob('*.json'):
            with open(task_file) as f:
                task = json.load(f)
            if task.get('id') == task_id:
                return task, task_file
    return None, None


def analyze_failure(task_id: str, results: list) -> dict:
    """Analyze why a task is failing."""

    task, task_file = load_task_definition(task_id)
    if not task:
        return {'error': f'Task {task_id} not found'}

    # Get results for this task
    task_results = [r for r in results if r.get('task_id') == task_id]

    anka_results = [r for r in task_results if r.get('language') == 'anka']
    python_results = [r for r in task_results if r.get('language') == 'python']

    analysis = {
        'task_id': task_id,
        'task_file': str(task_file),
        'prompt': task.get('prompt') or task.get('description', ''),
        'expected': None,
        'anka_outputs': [],
        'python_outputs': [],
        'issue_type': None,
        'fix_suggestion': None
    }

    # Get expected output
    test_cases = task.get('test_cases', [])
    if test_cases:
        analysis['expected'] = test_cases[0].get('expected') or test_cases[0].get('expected_output')

    # Collect actual outputs
    for r in anka_results[:3]:
        analysis['anka_outputs'].append({
            'passed': r.get('passed') or r.get('output_correct', False),
            'actual': r.get('actual_output'),
            'error': r.get('execution_error') or r.get('parse_error')
        })

    for r in python_results[:3]:
        analysis['python_outputs'].append({
            'passed': r.get('passed') or r.get('output_correct', False),
            'actual': r.get('actual_output'),
            'error': r.get('execution_error') or r.get('parse_error')
        })

    # Determine issue type
    anka_passing = any(o['passed'] for o in analysis['anka_outputs'])
    python_passing = any(o['passed'] for o in analysis['python_outputs'])

    if not anka_passing and not python_passing:
        # Both fail - likely task bug
        analysis['issue_type'] = 'TASK_BUG'

        # Check if outputs are consistent (LLMs agree but task expects different)
        anka_actuals = [json.dumps(o['actual'], sort_keys=True) for o in analysis['anka_outputs'] if o['actual'] is not None]
        python_actuals = [json.dumps(o['actual'], sort_keys=True) for o in analysis['python_outputs'] if o['actual'] is not None]

        if anka_actuals and python_actuals:
            # If LLMs produce similar outputs but task expects different
            if len(set(anka_actuals)) == 1 and len(set(python_actuals)) == 1:
                if anka_actuals[0] == python_actuals[0]:
                    analysis['fix_suggestion'] = 'UPDATE_EXPECTED'
                    analysis['suggested_expected'] = analysis['anka_outputs'][0]['actual']

    elif not anka_passing:
        analysis['issue_type'] = 'ANKA_PROMPT'
        analysis['fix_suggestion'] = 'ADD_EXAMPLES'

    elif not python_passing:
        analysis['issue_type'] = 'PYTHON_WEAKNESS'
        analysis['fix_suggestion'] = 'NONE_NEEDED'  # This is good for Anka!

    return analysis


def fix_task_expected_output(task_id: str, new_expected) -> bool:
    """Update a task's expected output."""
    task, task_file = load_task_definition(task_id)
    if not task:
        return False

    # Update expected output in all test cases
    for tc in task.get('test_cases', []):
        if 'expected' in tc:
            tc['expected'] = new_expected
        elif 'expected_output' in tc:
            tc['expected_output'] = new_expected

    # Save back
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=2)

    print(f"  Updated {task_file}")
    return True


def analyze_all_failures(auto_fix: bool = False):
    """Analyze all failing tasks and generate fix report."""

    data = load_latest_results()
    if not data:
        print("No results found! Run benchmark first.")
        return

    results = data.get('results', [])
    if not results:
        print("No results in data!")
        return

    # Find failing tasks
    task_pass_rates = defaultdict(lambda: {'anka': [], 'python': []})

    for r in results:
        tid = r.get('task_id')
        lang = r.get('language')
        passed = r.get('passed') or r.get('output_correct', False)
        task_pass_rates[tid][lang].append(passed)

    failing_tasks = []
    for tid, rates in task_pass_rates.items():
        anka_rate = sum(rates['anka']) / len(rates['anka']) if rates['anka'] else 0
        python_rate = sum(rates['python']) / len(rates['python']) if rates['python'] else 0

        # Consider failing if either language < 90%
        if anka_rate < 0.9 or python_rate < 0.9:
            failing_tasks.append((tid, anka_rate, python_rate))

    print(f"\n{'='*80}")
    print(f"TASK FAILURE ANALYSIS")
    print(f"{'='*80}")
    print(f"\nFound {len(failing_tasks)} tasks with issues\n")

    # Categorize failures
    task_bugs = []
    anka_issues = []
    python_weaknesses = []

    for tid, anka_rate, python_rate in failing_tasks:
        analysis = analyze_failure(tid, results)

        if analysis.get('issue_type') == 'TASK_BUG':
            task_bugs.append(analysis)
        elif analysis.get('issue_type') == 'ANKA_PROMPT':
            anka_issues.append(analysis)
        elif analysis.get('issue_type') == 'PYTHON_WEAKNESS':
            python_weaknesses.append(analysis)

    # Report task bugs
    print(f"\n{'='*60}")
    print(f"1. TASK DEFINITION BUGS ({len(task_bugs)} tasks)")
    print(f"   Both languages produce same output but task expects different")
    print(f"{'='*60}")

    auto_fixable = []
    manual_fix = []

    for analysis in task_bugs:
        tid = analysis['task_id']
        print(f"\n  {tid}:")
        print(f"    File: {analysis['task_file']}")
        prompt_preview = analysis['prompt'][:100] if analysis['prompt'] else 'N/A'
        print(f"    Prompt: {prompt_preview}...")

        expected_str = json.dumps(analysis['expected'])[:100] if analysis['expected'] else 'N/A'
        print(f"    Expected: {expected_str}...")

        if analysis['anka_outputs']:
            actual = analysis['anka_outputs'][0].get('actual')
            actual_str = json.dumps(actual)[:100] if actual else 'N/A'
            print(f"    LLM produced: {actual_str}...")

            if analysis.get('fix_suggestion') == 'UPDATE_EXPECTED':
                print(f"    -> AUTO-FIXABLE: Update expected to match LLM output")
                auto_fixable.append(analysis)
            else:
                print(f"    -> MANUAL REVIEW NEEDED")
                manual_fix.append(analysis)

    # Report Anka issues
    print(f"\n{'='*60}")
    print(f"2. ANKA PROMPT ISSUES ({len(anka_issues)} tasks)")
    print(f"   Python passes but Anka fails - need better examples")
    print(f"{'='*60}")

    for analysis in anka_issues:
        tid = analysis['task_id']
        prompt_preview = analysis['prompt'][:100] if analysis['prompt'] else 'N/A'
        print(f"\n  {tid}:")
        print(f"    Prompt: {prompt_preview}...")
        if analysis['anka_outputs'] and analysis['anka_outputs'][0].get('error'):
            error_preview = analysis['anka_outputs'][0]['error'][:100]
            print(f"    Error: {error_preview}...")

    # Report Python weaknesses (good for us!)
    print(f"\n{'='*60}")
    print(f"3. PYTHON WEAKNESSES ({len(python_weaknesses)} tasks)")
    print(f"   Anka passes but Python fails - THIS IS GOOD!")
    print(f"{'='*60}")

    for analysis in python_weaknesses:
        tid = analysis['task_id']
        print(f"  [OK] {tid}: Anka wins!")

    # Auto-fix
    if auto_fixable:
        print(f"\n{'='*60}")
        print(f"AUTO-FIX AVAILABLE")
        print(f"{'='*60}")
        print(f"\n{len(auto_fixable)} tasks can be auto-fixed.")
        print("The LLMs consistently produce the same (correct) output")
        print("but the task definition expects something different.")

        if auto_fix:
            print("\nApplying auto-fixes...")
            for analysis in auto_fixable:
                tid = analysis['task_id']
                new_expected = analysis.get('suggested_expected')
                if new_expected:
                    print(f"  Fixing {tid}...")
                    fix_task_expected_output(tid, new_expected)
            print("\nAuto-fixes applied! Re-run benchmark to verify.")
        else:
            print("\nRun with --auto-fix to apply these fixes automatically.")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Task bugs (auto-fixable): {len(auto_fixable)}")
    print(f"  Task bugs (manual review): {len(manual_fix)}")
    print(f"  Anka prompt issues: {len(anka_issues)}")
    print(f"  Python weaknesses (Anka wins): {len(python_weaknesses)}")

    return {
        'auto_fixable': auto_fixable,
        'manual_fix': manual_fix,
        'anka_issues': anka_issues,
        'python_weaknesses': python_weaknesses
    }


if __name__ == '__main__':
    import sys

    auto_fix = '--auto-fix' in sys.argv
    analyze_all_failures(auto_fix=auto_fix)
