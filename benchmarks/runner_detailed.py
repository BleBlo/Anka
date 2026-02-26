#!/usr/bin/env python3
"""
Enhanced benchmark runner with detailed metrics for DSL viability study.
"""

import argparse
import atexit
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.metrics import (
    DetailedResult,
    classify_parse_error,
    attempt_recovery,
    compute_language_metrics,
    LanguageMetrics,
)
from benchmarks.llm_client import AnthropicClient, OpenAIClient, LLMClient


class DetailedBenchmarkRunner:
    """Enhanced benchmark runner with detailed metrics tracking."""

    def __init__(self) -> None:
        """Initialize the runner."""
        self.anthropic: Optional[LLMClient] = None
        self.openai: Optional[LLMClient] = None
        self.prompts: dict[str, str] = {}

    def _get_client(self, provider: str, model: str) -> LLMClient:
        """Get or create LLM client for provider."""
        if provider == 'anthropic':
            if not self.anthropic:
                self.anthropic = AnthropicClient(model=model)
            return self.anthropic
        elif provider == 'openai':
            if not self.openai:
                self.openai = OpenAIClient(model=model)
            return self.openai
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def load_prompt(self, language: str) -> str:
        """Load the benchmark prompt for a language."""
        if language not in self.prompts:
            # Try benchmark prompt first, fall back to regular
            paths = [
                Path('benchmarks/prompts') / f'{language}_benchmark.md',
                Path('benchmarks/prompts') / f'{language}_prompt.md'
            ]
            for path in paths:
                if path.exists():
                    with open(path) as f:
                        self.prompts[language] = f.read()
                    break
            else:
                raise FileNotFoundError(f"No prompt found for {language}")
        return self.prompts[language]

    def load_tasks(self, categories: Optional[list[str]] = None, limit: Optional[int] = None) -> list[dict]:
        """Load task definitions."""
        tasks = []
        tasks_dirs = [Path('benchmarks/tasks'), Path('benchmarks/problems')]

        for tasks_dir in tasks_dirs:
            if not tasks_dir.exists():
                continue
            for cat_dir in tasks_dir.iterdir():
                if not cat_dir.is_dir():
                    continue
                if categories and cat_dir.name not in categories:
                    continue
                for task_file in cat_dir.glob('*.json'):
                    with open(task_file) as f:
                        task = json.load(f)
                        task['category'] = cat_dir.name
                        tasks.append(task)

        tasks.sort(key=lambda t: t['id'])
        if limit:
            tasks = tasks[:limit]

        return tasks

    def build_prompt(self, task: dict, language: str) -> str:
        """Build full prompt for LLM."""
        lang_prompt = self.load_prompt(language)

        task_description = task.get('prompt') or task.get('description', '')
        schema = json.dumps(task.get('input_schema', {}), indent=2)

        if language == 'anka':
            instruction = "Write a complete Anka PIPELINE to solve this task."
        else:
            instruction = "Write a Python function called `transform` that takes a `data` dict parameter to solve this task."

        return f"""{lang_prompt}

---

## Your Task

{task_description}

## Input Schema
```json
{schema}
```

## Instructions
{instruction}

Write only the code, no explanations.
"""

    def call_llm(self, provider: str, model: str, prompt: str, temperature: float) -> tuple[str, int]:
        """Call LLM and return (response, latency_ms)."""
        client = self._get_client(provider, model)

        start = time.time()
        result = client.generate(prompt=prompt, temperature=temperature)
        latency = int((time.time() - start) * 1000)

        return result.code, latency

    def extract_code(self, response: str, language: str) -> str:
        """Extract code block from LLM response."""
        import re

        # Try to find code block
        patterns = [
            rf'```{language}\s*(.*?)```',
            rf'```\s*(.*?)```',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # No code block - try to extract directly
        if language == 'anka' and 'PIPELINE' in response:
            start = response.find('PIPELINE')
            return response[start:].strip()

        if language == 'python' and 'def transform' in response:
            start = response.find('def transform')
            return response[start:].strip()

        return response.strip()

    def execute_anka(self, code: str, inputs: dict) -> tuple[bool, Any, Optional[str]]:
        """Execute Anka code. Returns (success, output, error_message)."""
        try:
            from anka.grammar.parser import Parser
            from anka.runtime.interpreter import Interpreter

            parser = Parser()
            ast = parser.parse(code)

            interp = Interpreter()
            result = interp.execute(ast, inputs)

            return True, result, None
        except Exception as e:
            return False, None, str(e)

    def execute_python(self, code: str, inputs: dict) -> tuple[bool, Any, Optional[str]]:
        """Execute Python code. Returns (success, output, error_message)."""
        try:
            namespace: dict[str, Any] = {'__builtins__': __builtins__}
            exec(code, namespace)

            if 'transform' not in namespace:
                return False, None, "No 'transform' function defined"

            # Call with the data dict
            result = namespace['transform'](inputs)

            return True, result, None
        except SyntaxError as e:
            return False, None, f"SyntaxError: {e}"
        except Exception as e:
            return False, None, str(e)

    def compare_outputs(self, actual: Any, expected: Any) -> bool:
        """Compare actual vs expected output."""
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False

        # Normalize for comparison
        def normalize(val: Any) -> Any:
            if isinstance(val, list):
                # Sort list of dicts by their JSON representation
                return sorted([normalize(v) for v in val], key=lambda x: json.dumps(x, sort_keys=True))
            elif isinstance(val, dict):
                return {k: normalize(v) for k, v in val.items()}
            elif isinstance(val, float):
                return round(val, 6)  # Handle float precision
            else:
                return val

        return normalize(actual) == normalize(expected)

    def run_single(
        self,
        task: dict,
        language: str,
        provider: str,
        model: str,
        sample: int,
        temperature: float
    ) -> DetailedResult:
        """Run a single benchmark sample with detailed tracking."""

        result = DetailedResult(
            task_id=task['id'],
            language=language,
            model=model,
            sample=sample,
            generated_code='',
            generation_time_ms=0,
            parse_success=False
        )

        # Stage 1: Generate code
        prompt = self.build_prompt(task, language)
        response, latency = self.call_llm(provider, model, prompt, temperature)
        code = self.extract_code(response, language)

        result.generated_code = code
        result.generation_time_ms = latency

        # Stage 2: Parse
        test_cases = task.get('test_cases', [])
        if not test_cases:
            result.parse_success = False
            result.parse_error = "No test cases defined"
            return result

        first_input = test_cases[0]['input']

        if language == 'anka':
            parse_success, _, parse_error = self.execute_anka(code, first_input)
        else:
            parse_success, _, parse_error = self.execute_python(code, first_input)

        # Check if it's a parse error vs runtime error
        if not parse_success and parse_error:
            error_lower = parse_error.lower()
            is_parse_error = any(x in error_lower for x in ['syntax', 'parse', 'unexpected', 'invalid', 'indent'])
            if is_parse_error:
                result.parse_success = False
                result.parse_error = parse_error
                result.parse_error_type = classify_parse_error(parse_error, code, language)
            else:
                # It parsed but failed at runtime
                result.parse_success = True
                result.execution_success = False
                result.execution_error = parse_error
        else:
            result.parse_success = parse_success

        # Stage 3: Recovery (if parse failed)
        if not result.parse_success and language == 'anka':
            recovery_success, recovered_code, method = attempt_recovery(code, result.parse_error or '', language)
            result.recovery_attempted = True

            if recovery_success and recovered_code != code:
                # Try to parse recovered code
                parse_success2, _, parse_error2 = self.execute_anka(recovered_code, first_input)
                if parse_success2 or (parse_error2 and 'syntax' not in parse_error2.lower()):
                    result.recovery_success = True
                    result.recovered_code = recovered_code
                    result.recovery_method = method
                    code = recovered_code  # Use recovered code for execution
                    result.parse_success = True  # Effectively parsed after recovery

        # Stage 4 & 5: Execute and compare outputs (for all test cases)
        if result.parse_success or result.recovery_success:
            all_correct = True
            last_output = None
            last_expected = None

            for tc in test_cases:
                tc_input = tc['input']
                # Use 'expected' if present (even if empty list), otherwise try 'expected_output'
                tc_expected = tc['expected'] if 'expected' in tc else tc.get('expected_output')

                if language == 'anka':
                    success, output, error = self.execute_anka(code, tc_input)
                else:
                    success, output, error = self.execute_python(code, tc_input)

                last_output = output
                last_expected = tc_expected

                if not success:
                    result.execution_success = False
                    result.execution_error = error
                    all_correct = False
                    break

                if not self.compare_outputs(output, tc_expected):
                    result.execution_success = True
                    result.output_correct = False
                    result.actual_output = output
                    result.expected_output = tc_expected
                    all_correct = False
                    break

            if all_correct:
                result.execution_success = True
                result.output_correct = True
                result.actual_output = last_output
                result.expected_output = last_expected

        return result

    def run_benchmark(
        self,
        provider: str = 'anthropic',
        model: str = 'claude-3-5-haiku-20241022',
        languages: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        samples: int = 5,
        temperature: float = 0.7,
        limit: Optional[int] = None
    ) -> dict:
        """Run full benchmark with detailed metrics."""

        if languages is None:
            languages = ['anka', 'python']

        tasks = self.load_tasks(categories, limit)
        print(f"Loaded {len(tasks)} tasks")

        total = len(tasks) * len(languages) * samples
        print(f"Running {total} benchmark samples...")

        results: list[DetailedResult] = []
        completed = 0

        # Setup progressive saving
        output_dir = Path('benchmarks/results')
        output_dir.mkdir(exist_ok=True)
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        output_path = output_dir / f"{run_id}.json"

        def save_progress() -> None:
            """Save current results to file."""
            if not results:
                return
            progress_output = {
                'run_id': run_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'in_progress',
                'config': {
                    'provider': provider,
                    'model': model,
                    'languages': languages,
                    'categories': categories or 'all',
                    'samples_per_task': samples,
                    'temperature': temperature,
                    'total_tasks': len(tasks)
                },
                'progress': f"{len(results)}/{total}",
                'results': [self._result_to_dict(r) for r in results]
            }
            with open(output_path, 'w') as f:
                json.dump(progress_output, f, indent=2, default=str)

        # Register to save on exit (even on crash)
        atexit.register(save_progress)

        for task in tasks:
            for language in languages:
                for sample in range(1, samples + 1):
                    result = self.run_single(
                        task=task,
                        language=language,
                        provider=provider,
                        model=model,
                        sample=sample,
                        temperature=temperature
                    )
                    results.append(result)

                    completed += 1
                    status_char = 'PASS' if result.passed else 'FAIL'
                    stage = result.final_status
                    print(f"[{completed}/{total}] {status_char} {task['id']} | {language} | sample {sample} | {stage}")

                    # Save every 10 samples
                    if completed % 10 == 0:
                        save_progress()

        # Unregister atexit since we're saving properly now
        atexit.unregister(save_progress)

        # Compute metrics
        anka_metrics = compute_language_metrics(results, 'anka', model)
        python_metrics = compute_language_metrics(results, 'python', model)

        output = {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'complete',
            'config': {
                'provider': provider,
                'model': model,
                'languages': languages,
                'categories': categories or 'all',
                'samples_per_task': samples,
                'temperature': temperature,
                'total_tasks': len(tasks)
            },
            'metrics': {
                'anka': self._metrics_to_dict(anka_metrics),
                'python': self._metrics_to_dict(python_metrics)
            },
            'results': [self._result_to_dict(r) for r in results]
        }

        # Save final results
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")
        self._print_summary(anka_metrics, python_metrics)

        return output

    def _metrics_to_dict(self, m: LanguageMetrics) -> dict:
        """Convert metrics to dictionary."""
        return {
            'total_samples': m.total_samples,
            'total_tasks': m.total_tasks,
            'overall_pass_rate': round(m.overall_pass_rate, 4),
            'overall_pass_count': m.overall_pass_count,
            'parse_success_rate': round(m.parse_success_rate, 4),
            'parse_success_count': m.parse_success_count,
            'recovery_eligible_count': m.recovery_eligible_count,
            'recovery_success_count': m.recovery_success_count,
            'recovery_rate': round(m.recovery_rate, 4),
            'pass_rate_with_recovery': round(m.pass_rate_with_recovery, 4),
            'execution_success_rate': round(m.execution_success_rate, 4),
            'output_correct_rate': round(m.output_correct_rate, 4),
            'avg_consistency_score': round(m.avg_consistency_score, 4),
            'fully_consistent_tasks': m.fully_consistent_tasks,
            'parse_error_count': m.parse_error_count,
            'runtime_error_count': m.runtime_error_count,
            'wrong_output_count': m.wrong_output_count,
            'by_category': m.metrics_by_category
        }

    def _result_to_dict(self, r: DetailedResult) -> dict:
        """Convert result to dictionary."""
        return {
            'task_id': r.task_id,
            'language': r.language,
            'model': r.model,
            'sample': r.sample,
            'generated_code': r.generated_code,
            'generation_time_ms': r.generation_time_ms,
            'parse_success': r.parse_success,
            'parse_error': r.parse_error,
            'parse_error_type': r.parse_error_type,
            'recovery_attempted': r.recovery_attempted,
            'recovery_success': r.recovery_success,
            'recovery_method': r.recovery_method,
            'execution_success': r.execution_success,
            'execution_error': r.execution_error,
            'output_correct': r.output_correct,
            'final_status': r.final_status,
            'passed': r.passed
        }

    def _print_summary(self, anka: LanguageMetrics, python: LanguageMetrics) -> None:
        """Print benchmark summary."""
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)

        print(f"\n{'Metric':<35} {'Anka':<15} {'Python':<15} {'Diff':<10}")
        print("-" * 75)

        def row(name: str, a_val: float, p_val: float, is_pct: bool = True) -> None:
            if is_pct:
                a_str = f"{a_val * 100:.1f}%"
                p_str = f"{p_val * 100:.1f}%"
                diff = f"{(a_val - p_val) * 100:+.1f}%"
            else:
                a_str = str(int(a_val)) if isinstance(a_val, float) and a_val == int(a_val) else str(a_val)
                p_str = str(int(p_val)) if isinstance(p_val, float) and p_val == int(p_val) else str(p_val)
                diff_val = a_val - p_val
                diff = f"{int(diff_val):+d}" if isinstance(diff_val, (int, float)) and diff_val == int(diff_val) else f"{diff_val:+.2f}"
            print(f"{name:<35} {a_str:<15} {p_str:<15} {diff:<10}")

        row("Overall Pass Rate", anka.overall_pass_rate, python.overall_pass_rate)
        row("Parse Success Rate", anka.parse_success_rate, python.parse_success_rate)
        row("Recovery Rate (of failures)", anka.recovery_rate, python.recovery_rate)
        row("Pass Rate (with recovery)", anka.pass_rate_with_recovery, python.pass_rate_with_recovery)
        row("Avg Consistency Score", anka.avg_consistency_score, python.avg_consistency_score)
        row("Fully Consistent Tasks", float(anka.fully_consistent_tasks), float(python.fully_consistent_tasks), False)

        print("\nError Breakdown:")
        row("  Parse Errors", float(anka.parse_error_count), float(python.parse_error_count), False)
        row("  Runtime Errors", float(anka.runtime_error_count), float(python.runtime_error_count), False)
        row("  Wrong Outputs", float(anka.wrong_output_count), float(python.wrong_output_count), False)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run detailed DSL benchmark")
    parser.add_argument('--provider', default='anthropic', choices=['anthropic', 'openai'])
    parser.add_argument('--model', default='claude-3-5-haiku-20241022')
    parser.add_argument('--languages', default='anka,python')
    parser.add_argument('--categories', default=None, help='Comma-separated categories')
    parser.add_argument('--samples', type=int, default=5)
    parser.add_argument('--temperature', type=float, default=0.7)
    parser.add_argument('--limit', type=int, default=None, help='Limit number of tasks')

    args = parser.parse_args()

    runner = DetailedBenchmarkRunner()
    runner.run_benchmark(
        provider=args.provider,
        model=args.model,
        languages=args.languages.split(','),
        categories=args.categories.split(',') if args.categories else None,
        samples=args.samples,
        temperature=args.temperature,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
