"""
Smart benchmark runner that:
1. Only tests failed/untested tasks
2. Shows real-time progress
3. Saves incrementally
4. Supports multiple models
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.optimization_tracker import OptimizationState, OptimizationIteration, TaskStatus
from benchmarks.runner_detailed import DetailedBenchmarkRunner


# Cheap models to test
CHEAP_MODELS = {
    'haiku': {
        'provider': 'anthropic',
        'model_id': 'claude-3-5-haiku-20241022',
        'cost_per_1k': 0.00025
    },
    'gpt4o-mini': {
        'provider': 'openai',
        'model_id': 'gpt-4o-mini',
        'cost_per_1k': 0.00015
    },
    'gemini-flash': {
        'provider': 'google',
        'model_id': 'gemini-1.5-flash',
        'cost_per_1k': 0.000075
    },
    'gemini-flash-8b': {
        'provider': 'google',
        'model_id': 'gemini-1.5-flash-8b',
        'cost_per_1k': 0.0000375
    }
}


class SmartRunner:
    """Smart benchmark runner with optimization tracking."""

    def __init__(self):
        self.state = OptimizationState.load()
        self.runner = DetailedBenchmarkRunner()
        self.all_tasks: Optional[List[dict]] = None

    def load_all_tasks(self) -> List[dict]:
        """Load all task definitions."""
        if self.all_tasks is None:
            self.all_tasks = self.runner.load_tasks()

            # Initialize task tracking
            for task in self.all_tasks:
                tid = task['id']
                if tid not in self.state.tasks:
                    category = task.get('category', tid.rsplit('_', 1)[0])
                    self.state.tasks[tid] = TaskStatus(task_id=tid, category=category)

        return self.all_tasks

    def run_focused(
        self,
        model_name: str = 'haiku',
        samples: int = 5,
        only_failing: bool = True,
        categories: Optional[List[str]] = None,
        max_tasks: Optional[int] = None
    ):
        """
        Run focused benchmark on failing tasks only.

        Args:
            model_name: Which model to use (haiku, gpt4o-mini, etc.)
            samples: Samples per task
            only_failing: If True, only test tasks that previously failed
            categories: Limit to specific categories
            max_tasks: Maximum number of tasks to test
        """
        model_config = CHEAP_MODELS.get(model_name)
        if not model_config:
            print(f"Unknown model: {model_name}")
            print(f"Available: {list(CHEAP_MODELS.keys())}")
            return

        provider = model_config['provider']
        model_id = model_config['model_id']

        # Track this model
        if model_name not in self.state.models:
            self.state.models.append(model_name)

        # Load tasks
        all_tasks = self.load_all_tasks()

        # Filter tasks
        if only_failing:
            task_ids_to_test = self.state.get_tasks_to_test(model_name)
        else:
            task_ids_to_test = [t['id'] for t in all_tasks]

        # Apply category filter
        if categories:
            task_ids_to_test = [
                tid for tid in task_ids_to_test
                if any(tid.startswith(cat) for cat in categories)
            ]

        # Apply max tasks limit
        if max_tasks:
            task_ids_to_test = task_ids_to_test[:max_tasks]

        tasks_to_test = [t for t in all_tasks if t['id'] in task_ids_to_test]

        if not tasks_to_test:
            print("No tasks to test! All tasks passing or none match filters.")
            self.state.print_summary()
            return

        print(f"\n{'='*70}")
        print(f"FOCUSED BENCHMARK RUN")
        print(f"{'='*70}")
        print(f"Model: {model_name} ({model_id})")
        print(f"Tasks to test: {len(tasks_to_test)}")
        print(f"Samples per task: {samples}")
        print(f"Total API calls: {len(tasks_to_test) * samples * 2}")
        print(f"{'='*70}\n")

        # Run benchmark
        results_by_task: Dict[str, Dict[str, List[bool]]] = defaultdict(lambda: {'anka': [], 'python': []})
        total = len(tasks_to_test) * samples * 2
        completed = 0
        start_time = time.time()

        for task in tasks_to_test:
            task_errors: List[str] = []

            for language in ['anka', 'python']:
                for sample in range(1, samples + 1):
                    try:
                        result = self.runner.run_single(
                            task=task,
                            language=language,
                            provider=provider,
                            model=model_id,
                            sample=sample,
                            temperature=0.7
                        )

                        passed = result.passed or result.output_correct
                        results_by_task[task['id']][language].append(passed)

                        if not passed and language == 'anka':
                            error = result.parse_error or result.execution_error or 'wrong_output'
                            task_errors.append(error[:100])

                        completed += 1

                        # Progress update
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        eta = (total - completed) / rate if rate > 0 else 0

                        status = "PASS" if passed else "FAIL"
                        print(f"\r[{completed}/{total}] {status} {task['id']} | {language} | "
                              f"sample {sample} | ETA: {eta:.0f}s   ", end='', flush=True)

                        # Save progress every 20 samples
                        if completed % 20 == 0:
                            self._update_state(results_by_task, model_name, task_errors)
                            self.state.save()

                    except Exception as e:
                        print(f"\nError on {task['id']}: {e}")
                        completed += 1
                        continue

            # Update state after each task
            self._update_state(results_by_task, model_name, task_errors)

        print("\n")

        # Final update
        self._update_state(results_by_task, model_name, [])

        # Calculate overall rates
        all_anka: List[bool] = []
        all_python: List[bool] = []
        for tid, results in results_by_task.items():
            all_anka.extend(results['anka'])
            all_python.extend(results['python'])

        anka_pass_rate = sum(all_anka) / len(all_anka) if all_anka else 0
        python_pass_rate = sum(all_python) / len(all_python) if all_python else 0

        # Record iteration
        iteration = OptimizationIteration(
            iteration=len(self.state.iterations) + 1,
            timestamp=datetime.now().isoformat(),
            model=model_name,
            tasks_tested=list(results_by_task.keys()),
            samples_per_task=samples,
            anka_pass_rate=anka_pass_rate,
            python_pass_rate=python_pass_rate,
            anka_parse_rate=0.99,  # TODO: track actual parse rate
        )
        self.state.add_iteration(iteration)
        self.state.save()

        # Print results
        self._print_results(results_by_task, model_name)
        self.state.print_summary()

    def _update_state(self, results_by_task: dict, model_name: str, errors: List[str]):
        """Update optimization state with results."""
        for tid, results in results_by_task.items():
            anka_results = results['anka']
            python_results = results['python']

            anka_rate = sum(anka_results) / len(anka_results) if anka_results else 0
            python_rate = sum(python_results) / len(python_results) if python_results else 0

            self.state.update_task(tid, model_name, anka_rate, python_rate, errors)

    def _print_results(self, results_by_task: dict, model_name: str):
        """Print results summary."""
        print(f"\n{'='*70}")
        print(f"RESULTS FOR {model_name}")
        print(f"{'='*70}")

        # By category
        by_category: Dict[str, Dict[str, List[bool]]] = defaultdict(lambda: {'anka': [], 'python': []})
        for tid, results in results_by_task.items():
            category = tid.rsplit('_', 1)[0]
            by_category[category]['anka'].extend(results['anka'])
            by_category[category]['python'].extend(results['python'])

        print(f"\n{'Category':<15} {'Anka':<12} {'Python':<12} {'Diff':<10}")
        print("-"*50)

        total_anka: List[bool] = []
        total_python: List[bool] = []

        for cat in sorted(by_category.keys()):
            anka = by_category[cat]['anka']
            python = by_category[cat]['python']

            anka_rate = sum(anka) / len(anka) if anka else 0
            python_rate = sum(python) / len(python) if python else 0
            diff = anka_rate - python_rate

            total_anka.extend(anka)
            total_python.extend(python)

            print(f"{cat:<15} {anka_rate*100:>6.1f}%      {python_rate*100:>6.1f}%      {diff*100:>+5.1f}%")

        print("-"*50)
        overall_anka = sum(total_anka) / len(total_anka) if total_anka else 0
        overall_python = sum(total_python) / len(total_python) if total_python else 0
        overall_diff = overall_anka - overall_python
        print(f"{'OVERALL':<15} {overall_anka*100:>6.1f}%      {overall_python*100:>6.1f}%      {overall_diff*100:>+5.1f}%")

    def run_full(self, model_name: str = 'haiku', samples: int = 10):
        """Run full benchmark on all tasks (for final publication results)."""
        print("\n" + "="*70)
        print("FULL BENCHMARK RUN (Publication Mode)")
        print("="*70)

        self.run_focused(
            model_name=model_name,
            samples=samples,
            only_failing=False,  # Test ALL tasks
            categories=None,
            max_tasks=None
        )

    def run_multi_model(self, samples: int = 5, only_failing: bool = True):
        """Run benchmark across all cheap models."""
        for model_name in CHEAP_MODELS.keys():
            print(f"\n\n{'#'*70}")
            print(f"# TESTING MODEL: {model_name}")
            print(f"{'#'*70}")

            try:
                self.run_focused(
                    model_name=model_name,
                    samples=samples,
                    only_failing=only_failing
                )
            except Exception as e:
                print(f"Error with {model_name}: {e}")
                continue

    def show_failing_tasks(self):
        """Show tasks that need attention."""
        self.load_all_tasks()

        print("\n" + "="*70)
        print("TASKS NEEDING ATTENTION")
        print("="*70)

        failing = []
        for tid, task in self.state.tasks.items():
            if task.needs_attention:
                failing.append(task)

        if not failing:
            print("\nAll tasks passing! Ready for full benchmark.")
            return

        # Group by category
        by_category: Dict[str, List[TaskStatus]] = defaultdict(list)
        for task in failing:
            by_category[task.category].append(task)

        for cat in sorted(by_category.keys()):
            tasks = by_category[cat]
            print(f"\n{cat.upper()} ({len(tasks)} failing):")

            for task in tasks:
                # Show pass rates per model
                rates = []
                for model in task.results:
                    rate = task.anka_pass_rate(model)
                    rates.append(f"{model}: {rate*100:.0f}%")

                is_bug = any(task.is_task_bug(m) for m in task.results)
                bug_marker = " [TASK BUG?]" if is_bug else ""

                print(f"  {task.task_id}: {', '.join(rates)}{bug_marker}")

                if task.common_errors:
                    print(f"    Errors: {task.common_errors[0][:60]}...")

    def suggest_fixes(self):
        """Analyze failures and suggest fixes."""
        print("\n" + "="*70)
        print("SUGGESTED FIXES")
        print("="*70)

        task_bugs = []
        prompt_issues = []
        grammar_gaps = []
        runtime_bugs = []

        for tid, task in self.state.tasks.items():
            if not task.needs_attention:
                continue

            # Check if task bug (both languages fail)
            is_task_bug = any(task.is_task_bug(m) for m in task.results)

            if is_task_bug:
                task_bugs.append(task)
            elif any('parse' in e.lower() for e in task.common_errors):
                grammar_gaps.append(task)
            elif any('runtime' in e.lower() or 'execution' in e.lower() for e in task.common_errors):
                runtime_bugs.append(task)
            else:
                prompt_issues.append(task)

        if task_bugs:
            print(f"\n1. TASK DEFINITION BUGS ({len(task_bugs)} tasks)")
            print("   Both Anka and Python fail - fix the task JSON")
            for t in task_bugs[:5]:
                print(f"   - {t.task_id}")

        if grammar_gaps:
            print(f"\n2. GRAMMAR GAPS ({len(grammar_gaps)} tasks)")
            print("   Anka parse errors - add grammar aliases")
            for t in grammar_gaps[:5]:
                print(f"   - {t.task_id}: {t.common_errors[0][:50] if t.common_errors else 'N/A'}")

        if runtime_bugs:
            print(f"\n3. RUNTIME BUGS ({len(runtime_bugs)} tasks)")
            print("   Anka execution errors - fix interpreter")
            for t in runtime_bugs[:5]:
                print(f"   - {t.task_id}: {t.common_errors[0][:50] if t.common_errors else 'N/A'}")

        if prompt_issues:
            print(f"\n4. PROMPT ISSUES ({len(prompt_issues)} tasks)")
            print("   Anka wrong output - add examples to prompt")
            for t in prompt_issues[:5]:
                print(f"   - {t.task_id}")

        print(f"\nPriority: Fix task bugs first, then grammar, then prompt, then runtime")

    def analyze_by_difficulty(self):
        """Analyze results by difficulty level."""
        self.load_all_tasks()

        print("\n" + "="*70)
        print("RESULTS BY DIFFICULTY")
        print("="*70)

        # Build task difficulty map
        task_difficulty: Dict[str, str] = {}
        for task in self.all_tasks or []:
            task_difficulty[task['id']] = task.get('difficulty', 'easy')

        by_difficulty: Dict[str, Dict[str, List[float]]] = {
            'easy': {'anka': [], 'python': []},
            'medium': {'anka': [], 'python': []},
            'hard': {'anka': [], 'python': []}
        }

        for tid, task in self.state.tasks.items():
            difficulty = task_difficulty.get(tid, 'easy')
            for model in task.results:
                by_difficulty[difficulty]['anka'].append(task.anka_pass_rate(model))
                by_difficulty[difficulty]['python'].append(task.python_pass_rate(model))

        print(f"\n{'Difficulty':<12} {'Tasks':<8} {'Anka Avg':<12} {'Python Avg':<12} {'Advantage':<10}")
        print("-"*55)

        for diff in ['easy', 'medium', 'hard']:
            anka_rates = by_difficulty[diff]['anka']
            python_rates = by_difficulty[diff]['python']

            if not anka_rates:
                continue

            anka_avg = sum(anka_rates) / len(anka_rates)
            python_avg = sum(python_rates) / len(python_rates) if python_rates else 0
            advantage = anka_avg - python_avg
            task_count = len(anka_rates)

            print(f"{diff:<12} {task_count:<8} {anka_avg*100:>6.1f}%      {python_avg*100:>6.1f}%      {advantage*100:>+5.1f}%")

    def analyze_by_domain(self):
        """Analyze results by domain (general, finance, etc.)."""
        self.load_all_tasks()

        print("\n" + "="*70)
        print("RESULTS BY DOMAIN")
        print("="*70)

        # Build task domain map
        task_domain: Dict[str, str] = {}
        for task in self.all_tasks or []:
            task_domain[task['id']] = task.get('domain', 'general')

        by_domain: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: {'anka': [], 'python': []})

        for tid, task in self.state.tasks.items():
            domain = task_domain.get(tid, 'general')
            for model in task.results:
                by_domain[domain]['anka'].append(task.anka_pass_rate(model))
                by_domain[domain]['python'].append(task.python_pass_rate(model))

        print(f"\n{'Domain':<15} {'Tasks':<8} {'Anka Avg':<12} {'Python Avg':<12} {'Advantage':<10}")
        print("-"*60)

        for domain in sorted(by_domain.keys()):
            anka_rates = by_domain[domain]['anka']
            python_rates = by_domain[domain]['python']

            if not anka_rates:
                continue

            anka_avg = sum(anka_rates) / len(anka_rates)
            python_avg = sum(python_rates) / len(python_rates) if python_rates else 0
            advantage = anka_avg - python_avg
            task_count = len(anka_rates)

            print(f"{domain:<15} {task_count:<8} {anka_avg*100:>6.1f}%      {python_avg*100:>6.1f}%      {advantage*100:>+5.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Smart Anka Benchmark Runner")

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Focused run
    focus_parser = subparsers.add_parser('focus', help='Run on failing tasks only')
    focus_parser.add_argument('--model', default='haiku', choices=list(CHEAP_MODELS.keys()))
    focus_parser.add_argument('--samples', type=int, default=5)
    focus_parser.add_argument('--categories', help='Comma-separated categories')
    focus_parser.add_argument('--max-tasks', type=int, help='Max tasks to test')
    focus_parser.add_argument('--all', action='store_true', help='Test all tasks, not just failing')

    # Full run
    full_parser = subparsers.add_parser('full', help='Full benchmark (publication mode)')
    full_parser.add_argument('--model', default='haiku', choices=list(CHEAP_MODELS.keys()))
    full_parser.add_argument('--samples', type=int, default=10)

    # Multi-model run
    multi_parser = subparsers.add_parser('multi', help='Test across all models')
    multi_parser.add_argument('--samples', type=int, default=5)
    multi_parser.add_argument('--all', action='store_true', help='Test all tasks')

    # Status commands
    subparsers.add_parser('status', help='Show optimization status')
    subparsers.add_parser('failing', help='Show failing tasks')
    subparsers.add_parser('suggest', help='Suggest fixes')
    subparsers.add_parser('difficulty', help='Analyze by difficulty level')
    subparsers.add_parser('domain', help='Analyze by domain')

    args = parser.parse_args()

    runner = SmartRunner()

    if args.command == 'focus':
        categories = args.categories.split(',') if args.categories else None
        runner.run_focused(
            model_name=args.model,
            samples=args.samples,
            only_failing=not args.all,
            categories=categories,
            max_tasks=args.max_tasks
        )

    elif args.command == 'full':
        runner.run_full(model_name=args.model, samples=args.samples)

    elif args.command == 'multi':
        runner.run_multi_model(samples=args.samples, only_failing=not args.all)

    elif args.command == 'status':
        runner.state.print_summary()

    elif args.command == 'failing':
        runner.show_failing_tasks()

    elif args.command == 'suggest':
        runner.suggest_fixes()

    elif args.command == 'difficulty':
        runner.analyze_by_difficulty()

    elif args.command == 'domain':
        runner.analyze_by_domain()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
