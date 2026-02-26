"""
Interactive review and fix for specific benchmark tasks.
"""

import json
import sys
from pathlib import Path


def review_task(task_id: str):
    """Interactive review and fix for a specific task."""

    # Load task
    task = None
    task_file = None
    for base in ['benchmarks/tasks', 'benchmarks/problems']:
        for f in Path(base).rglob('*.json'):
            with open(f) as fp:
                t = json.load(fp)
            if t.get('id') == task_id:
                task = t
                task_file = f
                break

    if not task:
        print(f"Task {task_id} not found!")
        return

    print(f"\n{'='*70}")
    print(f"REVIEWING: {task_id}")
    print(f"{'='*70}")
    print(f"File: {task_file}")

    print(f"\n[PROMPT]")
    print(task.get('prompt') or task.get('description', 'N/A'))

    print(f"\n[INPUT SCHEMA]")
    print(json.dumps(task.get('input_schema', {}), indent=2))

    print(f"\n[TEST CASES]")
    for i, tc in enumerate(task.get('test_cases', [])):
        print(f"\n  Test Case {i+1}:")
        print(f"  Input:")
        print(json.dumps(tc.get('input', {}), indent=4))
        print(f"  Expected:")
        expected = tc.get('expected') or tc.get('expected_output')
        print(json.dumps(expected, indent=4))

    # Load results to see what LLM produced
    results_dir = Path('benchmarks/results')
    result_files = sorted(results_dir.glob('run_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)

    task_results = []
    if result_files:
        with open(result_files[0]) as f:
            results_data = json.load(f)

        task_results = [r for r in results_data.get('results', []) if r.get('task_id') == task_id]

        print(f"\n[LLM OUTPUTS]")
        for lang in ['anka', 'python']:
            lang_results = [r for r in task_results if r.get('language') == lang]
            if lang_results:
                r = lang_results[0]
                status = "PASS" if r.get('passed') or r.get('output_correct') else "FAIL"
                print(f"\n  {lang.upper()} ({status}):")

                if r.get('actual_output') is not None:
                    print(f"  Actual output:")
                    print(json.dumps(r.get('actual_output'), indent=4))

                if r.get('execution_error'):
                    print(f"  Error: {r.get('execution_error')}")

                if r.get('parse_error'):
                    print(f"  Parse error: {r.get('parse_error')}")

    # Options
    print(f"\n{'='*70}")
    print("OPTIONS:")
    print("  1. Update expected output to match LLM output (Anka)")
    print("  2. Update expected output to match LLM output (Python)")
    print("  3. Edit expected output manually")
    print("  4. Edit prompt/description")
    print("  5. Skip (no changes)")
    print("  q. Quit")

    choice = input("\nChoice: ").strip()

    if choice == '1':
        # Use Anka output
        anka_results = [r for r in task_results if r.get('language') == 'anka']
        if anka_results and anka_results[0].get('actual_output') is not None:
            new_expected = anka_results[0]['actual_output']
            for tc in task['test_cases']:
                tc['expected'] = new_expected
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            print(f"Updated {task_file}")

    elif choice == '2':
        # Use Python output
        python_results = [r for r in task_results if r.get('language') == 'python']
        if python_results and python_results[0].get('actual_output') is not None:
            new_expected = python_results[0]['actual_output']
            for tc in task['test_cases']:
                tc['expected'] = new_expected
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            print(f"Updated {task_file}")

    elif choice == '3':
        # Manual edit
        print("Enter new expected output as JSON (or 'cancel'):")
        new_json = input().strip()
        if new_json.lower() != 'cancel':
            try:
                new_expected = json.loads(new_json)
                for tc in task['test_cases']:
                    tc['expected'] = new_expected
                with open(task_file, 'w') as f:
                    json.dump(task, f, indent=2)
                print(f"Updated {task_file}")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")

    elif choice == '4':
        # Edit prompt
        print(f"Current prompt: {task.get('prompt') or task.get('description')}")
        print("Enter new prompt (or 'cancel'):")
        new_prompt = input().strip()
        if new_prompt.lower() != 'cancel':
            task['prompt'] = new_prompt
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            print(f"Updated {task_file}")

    elif choice == 'q':
        sys.exit(0)


def review_all_failing():
    """Review all failing tasks interactively."""

    # Load optimization state to find failing tasks
    state_file = Path('benchmarks/optimization_state.json')
    if not state_file.exists():
        print("No optimization state found!")
        return

    with open(state_file) as f:
        state = json.load(f)

    failing_tasks = []
    for tid, task in state.get('tasks', {}).items():
        if task.get('needs_attention', True):
            failing_tasks.append(tid)

    print(f"Found {len(failing_tasks)} failing tasks")

    for tid in sorted(failing_tasks):
        review_task(tid)
        print("\n")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        review_task(sys.argv[1])
    else:
        review_all_failing()
