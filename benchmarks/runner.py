"""Benchmark runner for LLM code generation comparison.

Compares LLM accuracy between Anka DSL and Python for data transformations.

Usage:
    python -m benchmarks.runner --mock --tasks 3
    python -m benchmarks.runner --provider anthropic --samples 10
"""

import argparse
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from benchmarks.llm_client import LLMClient, get_llm_client
from benchmarks.prompts import load_prompt
from benchmarks.sandbox import Executor, compare_outputs, get_executor
from benchmarks.schema import BenchmarkRun, BenchmarkTask, TaskResult


def load_tasks(
    problems_dir: Optional[Path] = None,
    limit: Optional[int] = None,
    categories: Optional[list[str]] = None,
) -> list[BenchmarkTask]:
    """Load benchmark tasks from the problems/tasks directory.

    Args:
        problems_dir: Directory containing task JSON files.
        limit: Maximum number of tasks to load.
        categories: Only load tasks from these categories.

    Returns:
        List of BenchmarkTask objects.
    """
    if problems_dir is None:
        # Try 'tasks' directory first, fall back to 'problems'
        tasks_dir = Path(__file__).parent / "tasks"
        problems_dir = tasks_dir if tasks_dir.exists() else Path(__file__).parent / "problems"

    tasks = []
    for task_file in sorted(problems_dir.glob("**/*.json")):
        task = BenchmarkTask.from_json_file(task_file)
        if categories and task.category not in categories:
            continue
        tasks.append(task)
        if limit and len(tasks) >= limit:
            break

    return tasks


class BenchmarkRunner:
    """Runs benchmarks comparing Anka vs Python code generation."""

    def __init__(
        self,
        llm: LLMClient,
        temperature: float = 0.0,
        verbose: bool = False,
    ) -> None:
        """Initialize the benchmark runner.

        Args:
            llm: LLM client for code generation.
            temperature: Sampling temperature for generation.
            verbose: Whether to print detailed output.
        """
        self.llm = llm
        self.temperature = temperature
        self.verbose = verbose
        self._executors: dict[str, Executor] = {}

    def _get_executor(self, language: str) -> Executor:
        """Get or create an executor for a language."""
        if language not in self._executors:
            self._executors[language] = get_executor(language)
        return self._executors[language]

    def run_task(
        self,
        task: BenchmarkTask,
        language: str,
    ) -> TaskResult:
        """Run a single task and return the result.

        Args:
            task: The benchmark task to run.
            language: "anka" or "python".

        Returns:
            TaskResult with pass/fail status and details.
        """
        # Generate prompt
        prompt = load_prompt(language, task)

        # Generate code
        gen_result = self.llm.generate(
            prompt=prompt,
            temperature=self.temperature,
        )

        if self.verbose:
            print(f"  Generated {language} code:")
            for line in gen_result.code.split("\n")[:5]:
                print(f"    {line}")
            if len(gen_result.code.split("\n")) > 5:
                print("    ...")

        # Execute and test
        executor = self._get_executor(language)
        test_results: list[bool] = []
        error: Optional[str] = None

        for i, test_case in enumerate(task.test_cases):
            exec_result = executor.execute(gen_result.code, test_case.input)

            if not exec_result.success:
                error = exec_result.error
                test_results.append(False)
                if self.verbose:
                    print(f"  Test {i + 1}: FAIL (execution error)")
                    print(f"    {error}")
            else:
                passed = compare_outputs(exec_result.output, test_case.expected_output)
                test_results.append(passed)
                if self.verbose:
                    status = "PASS" if passed else "FAIL"
                    print(f"  Test {i + 1}: {status}")
                    if not passed:
                        print(f"    Expected: {test_case.expected_output}")
                        print(f"    Got: {exec_result.output}")

        return TaskResult(
            task_id=task.id,
            category=task.category,
            language=language,
            model=self.llm.model_name,
            generated_code=gen_result.code,
            test_results=test_results,
            pass_all=all(test_results),
            error=error,
            latency_ms=gen_result.latency_ms,
        )

    def run_all(
        self,
        tasks: list[BenchmarkTask],
        languages: list[str],
        n_samples: int = 1,
    ) -> BenchmarkRun:
        """Run all tasks for all languages.

        Args:
            tasks: List of tasks to run.
            languages: Languages to test (e.g., ["anka", "python"]).
            n_samples: Number of samples per task/language combination.

        Returns:
            BenchmarkRun with all results.
        """
        run = BenchmarkRun(
            run_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            model=self.llm.model_name,
            temperature=self.temperature,
        )

        total = len(tasks) * len(languages) * n_samples
        current = 0

        for task in tasks:
            print(f"\nTask: {task.id} ({task.category})")
            print(f"  {task.description}")

            for language in languages:
                for sample in range(n_samples):
                    current += 1
                    print(f"\n[{current}/{total}] {task.id} - {language}", end="")
                    if n_samples > 1:
                        print(f" (sample {sample + 1})")
                    else:
                        print()

                    result = self.run_task(task, language)
                    run.results.append(result)

                    status = "PASS" if result.pass_all else "FAIL"
                    passed = sum(result.test_results)
                    total_tests = len(result.test_results)
                    print(f"  Result: {status} ({passed}/{total_tests} tests)")

        return run


def print_summary(run: BenchmarkRun) -> None:
    """Print a summary of the benchmark run."""
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Run ID: {run.run_id}")
    print(f"Model: {run.model}")
    print(f"Temperature: {run.temperature}")
    print(f"Timestamp: {run.timestamp}")
    print()

    # Group by language
    by_language: dict[str, list[TaskResult]] = {}
    for result in run.results:
        if result.language not in by_language:
            by_language[result.language] = []
        by_language[result.language].append(result)

    # Print language summaries
    for language, results in sorted(by_language.items()):
        passed = sum(1 for r in results if r.pass_all)
        total = len(results)
        rate = passed / total * 100 if total > 0 else 0
        print(f"{language.upper():10} {passed:3}/{total:3} passed ({rate:5.1f}%)")

    # Print category breakdown
    print("\nBy Category:")
    categories: dict[str, dict[str, list[TaskResult]]] = {}
    for result in run.results:
        if result.category not in categories:
            categories[result.category] = {}
        if result.language not in categories[result.category]:
            categories[result.category][result.language] = []
        categories[result.category][result.language].append(result)

    for cat, langs in sorted(categories.items()):
        print(f"\n  {cat}:")
        for lang, results in sorted(langs.items()):
            passed = sum(1 for r in results if r.pass_all)
            total = len(results)
            rate = passed / total * 100 if total > 0 else 0
            print(f"    {lang:8} {passed:2}/{total:2} ({rate:5.1f}%)")


def main() -> int:
    """Run the benchmark suite."""
    parser = argparse.ArgumentParser(
        description="Anka LLM Benchmark Suite",
    )
    parser.add_argument(
        "--languages",
        default="anka,python",
        help="Comma-separated list of languages to test",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1,
        help="Number of samples per task/language",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--tasks",
        type=int,
        help="Limit number of tasks",
    )
    parser.add_argument(
        "--categories",
        help="Comma-separated list of categories to test",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        help="LLM provider: mock, anthropic, openai",
    )
    parser.add_argument(
        "--model",
        help="Model ID for the provider",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock LLM (same as --provider mock)",
    )
    parser.add_argument(
        "--output",
        help="Output file for results JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Anka LLM Benchmark Suite")
    print("=" * 60)

    # Parse languages
    languages = [lang.strip() for lang in args.languages.split(",")]
    print(f"Languages: {languages}")

    # Parse categories
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]
        print(f"Categories: {categories}")

    # Get LLM client
    provider = "mock" if args.mock else args.provider
    try:
        llm = get_llm_client(provider=provider, model=args.model)
        print(f"Provider: {provider}")
        print(f"Model: {llm.model_name}")
    except Exception as e:
        print(f"Error creating LLM client: {e}")
        return 1

    # Load tasks
    tasks = load_tasks(limit=args.tasks, categories=categories)
    print(f"Tasks: {len(tasks)}")

    if not tasks:
        print("No tasks found. Add task definitions to benchmarks/problems/")
        return 1

    # Run benchmarks
    runner = BenchmarkRunner(
        llm=llm,
        temperature=args.temperature,
        verbose=args.verbose,
    )

    run = runner.run_all(
        tasks=tasks,
        languages=languages,
        n_samples=args.samples,
    )

    # Print summary
    print_summary(run)

    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        output_path = results_dir / f"run_{run.run_id}.json"

    run.save(output_path)
    print(f"\nResults saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
