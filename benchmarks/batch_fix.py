"""
Batch fix common patterns in benchmark tasks.
"""

import json
from pathlib import Path


def fix_output_format_issues():
    """Fix common output format issues in tasks."""

    fixes_applied = 0

    # Common fixes:
    # 1. Expected is scalar but should be list
    # 2. Column names don't match prompt
    # 3. Expected uses 'expected_output' instead of 'expected'

    # Fix ALL task directories
    for base in ['benchmarks/tasks']:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for task_file in base_path.rglob('*.json'):
            with open(task_file) as f:
                task = json.load(f)

            modified = False

            for tc in task.get('test_cases', []):
                # Fix 1: Normalize to 'expected' key
                if 'expected_output' in tc and 'expected' not in tc:
                    tc['expected'] = tc.pop('expected_output')
                    modified = True

                # Fix 2: Ensure expected is a list
                expected = tc.get('expected')
                if expected is not None and not isinstance(expected, list):
                    # Wrap scalar in list with appropriate key
                    if isinstance(expected, (int, float)):
                        tc['expected'] = [{'result': expected}]
                        modified = True
                    elif isinstance(expected, dict):
                        tc['expected'] = [expected]
                        modified = True

            if modified:
                with open(task_file, 'w') as f:
                    json.dump(task, f, indent=2)
                print(f"Fixed: {task_file}")
                fixes_applied += 1

    print(f"\nApplied {fixes_applied} fixes")


def verify_task_structure():
    """Verify all tasks have correct structure."""

    issues = []

    # Only check benchmarks/tasks - problems/ is deprecated
    for base in ['benchmarks/tasks']:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for task_file in base_path.rglob('*.json'):
            with open(task_file) as f:
                task = json.load(f)

            tid = task.get('id', 'UNKNOWN')

            # Check required fields
            if not task.get('id'):
                issues.append(f"{task_file}: Missing 'id'")

            if not task.get('description') and not task.get('prompt'):
                issues.append(f"{task_file}: Missing 'description' or 'prompt'")

            if not task.get('input_schema'):
                issues.append(f"{task_file}: Missing 'input_schema'")

            if not task.get('test_cases'):
                issues.append(f"{task_file}: Missing 'test_cases'")
            else:
                for i, tc in enumerate(task['test_cases']):
                    if not tc.get('input'):
                        issues.append(f"{tid} test {i}: Missing 'input'")
                    # Allow empty lists as valid expected output
                    if 'expected' not in tc and 'expected_output' not in tc:
                        issues.append(f"{tid} test {i}: Missing 'expected'")

    if issues:
        print("STRUCTURE ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("All tasks have correct structure!")

    return issues


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify_task_structure()
    else:
        fix_output_format_issues()
        verify_task_structure()
