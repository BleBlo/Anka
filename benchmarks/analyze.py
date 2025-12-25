"""Statistical analysis for benchmark results.

Computes:
- pass@k metrics (probability of at least 1 correct in k attempts)
- Confidence intervals
- McNemar's test for paired comparison
- Category-level breakdown
- Error classification

Usage:
    python -m benchmarks.analyze results/run_xxx.json
    python -m benchmarks.analyze results/run_xxx.json --report
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from benchmarks.schema import BenchmarkRun, TaskResult


@dataclass
class PassAtKResult:
    """Pass@k metric result.

    Attributes:
        k: Number of attempts.
        pass_rate: Probability of at least one success in k attempts.
        ci_lower: 95% confidence interval lower bound.
        ci_upper: 95% confidence interval upper bound.
    """

    k: int
    pass_rate: float
    ci_lower: float
    ci_upper: float


@dataclass
class CategoryAnalysis:
    """Analysis for a specific category."""

    category: str
    anka_passed: int
    anka_total: int
    python_passed: int
    python_total: int

    @property
    def anka_rate(self) -> float:
        """Anka pass rate."""
        return self.anka_passed / self.anka_total if self.anka_total > 0 else 0.0

    @property
    def python_rate(self) -> float:
        """Python pass rate."""
        return self.python_passed / self.python_total if self.python_total > 0 else 0.0


@dataclass
class McNemarResult:
    """Result of McNemar's test for paired comparison."""

    # Contingency table
    both_pass: int  # Both Anka and Python pass
    anka_only: int  # Only Anka passes
    python_only: int  # Only Python passes
    both_fail: int  # Both fail

    chi_squared: float
    p_value: float
    significant: bool  # At alpha=0.05


@dataclass
class ErrorBreakdown:
    """Breakdown of error types."""

    parse_errors: int = 0
    runtime_errors: int = 0
    wrong_output: int = 0
    timeout_errors: int = 0
    other_errors: int = 0


@dataclass
class Analysis:
    """Complete benchmark analysis."""

    run_id: str
    model: str
    temperature: float
    total_tasks: int

    # Overall pass rates
    anka_passed: int = 0
    anka_total: int = 0
    python_passed: int = 0
    python_total: int = 0

    # Pass@k metrics
    anka_pass_at_1: Optional[PassAtKResult] = None
    python_pass_at_1: Optional[PassAtKResult] = None

    # By category
    by_category: list[CategoryAnalysis] = field(default_factory=list)

    # Statistical comparison
    mcnemar: Optional[McNemarResult] = None

    # Error analysis
    anka_errors: ErrorBreakdown = field(default_factory=ErrorBreakdown)
    python_errors: ErrorBreakdown = field(default_factory=ErrorBreakdown)

    @property
    def anka_rate(self) -> float:
        """Anka overall pass rate."""
        return self.anka_passed / self.anka_total if self.anka_total > 0 else 0.0

    @property
    def python_rate(self) -> float:
        """Python overall pass rate."""
        return self.python_passed / self.python_total if self.python_total > 0 else 0.0


def compute_pass_at_k(n: int, c: int, k: int) -> float:
    """Compute pass@k metric.

    Args:
        n: Total number of samples generated.
        c: Number of correct samples.
        k: Number of attempts (k in pass@k).

    Returns:
        pass@k probability.

    Note:
        Uses the unbiased estimator from the Codex paper:
        pass@k = 1 - C(n-c, k) / C(n, k)
    """
    if n - c < k:
        return 1.0
    if k == 0:
        return 0.0

    # Compute using logarithms for numerical stability
    log_numerator = sum(math.log(n - c - i) for i in range(k))
    log_denominator = sum(math.log(n - i) for i in range(k))

    return 1.0 - math.exp(log_numerator - log_denominator)


def compute_confidence_interval(
    pass_rate: float,
    n_samples: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Compute confidence interval for pass rate using Wilson score interval.

    Args:
        pass_rate: Observed pass rate.
        n_samples: Number of samples.
        confidence: Confidence level (default 0.95 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if n_samples == 0:
        return (0.0, 1.0)

    # Z-score for confidence level
    z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%

    # Wilson score interval
    denominator = 1 + z * z / n_samples
    center = (pass_rate + z * z / (2 * n_samples)) / denominator
    spread = (
        z
        * math.sqrt(
            pass_rate * (1 - pass_rate) / n_samples + z * z / (4 * n_samples * n_samples)
        )
        / denominator
    )

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return (lower, upper)


def mcnemar_test(
    both_pass: int,
    anka_only: int,
    python_only: int,
    both_fail: int,
) -> McNemarResult:
    """Perform McNemar's test for paired comparison.

    Args:
        both_pass: Number of tasks where both pass.
        anka_only: Number of tasks where only Anka passes.
        python_only: Number of tasks where only Python passes.
        both_fail: Number of tasks where both fail.

    Returns:
        McNemarResult with test statistics.
    """
    # McNemar's chi-squared statistic (with continuity correction)
    n_discordant = anka_only + python_only
    if n_discordant == 0:
        chi_squared = 0.0
        p_value = 1.0
    else:
        chi_squared = (abs(anka_only - python_only) - 1) ** 2 / n_discordant
        # p-value from chi-squared distribution with 1 df
        # Using approximation for simplicity
        p_value = 1.0 - chi_squared_cdf(chi_squared, 1)

    return McNemarResult(
        both_pass=both_pass,
        anka_only=anka_only,
        python_only=python_only,
        both_fail=both_fail,
        chi_squared=chi_squared,
        p_value=p_value,
        significant=p_value < 0.05,
    )


def chi_squared_cdf(x: float, df: int) -> float:
    """Approximate chi-squared CDF.

    Args:
        x: Chi-squared value.
        df: Degrees of freedom.

    Returns:
        Approximate CDF value.
    """
    if x <= 0:
        return 0.0

    # Simple approximation for df=1
    # Using the regularized incomplete gamma function approximation
    k = df / 2
    theta = 2

    # Gamma function approximation
    from math import exp, sqrt

    z = x / theta
    if z > 20:
        return 1.0

    # Series expansion for gamma distribution CDF
    term = exp(-z / 2) * sqrt(z / (2 * 3.14159))
    return 1.0 - 2 * term if df == 1 else min(1.0, z / (df + z))


def classify_error(error: Optional[str]) -> str:
    """Classify an error message into a category.

    Args:
        error: The error message.

    Returns:
        Error category: "parse", "runtime", "timeout", or "other".
    """
    if not error:
        return "other"

    error_lower = error.lower()

    if "parse" in error_lower or "syntax" in error_lower or "unexpected" in error_lower:
        return "parse"
    if "timeout" in error_lower:
        return "timeout"
    if "runtime" in error_lower or "error" in error_lower:
        return "runtime"
    return "other"


def analyze_run(run: BenchmarkRun) -> Analysis:
    """Analyze a benchmark run.

    Args:
        run: The benchmark run to analyze.

    Returns:
        Analysis with all metrics.
    """
    analysis = Analysis(
        run_id=run.run_id,
        model=run.model,
        temperature=run.temperature,
        total_tasks=len(set(r.task_id for r in run.results)),
    )

    # Separate by language
    anka_results = [r for r in run.results if r.language == "anka"]
    python_results = [r for r in run.results if r.language == "python"]

    # Overall pass rates
    analysis.anka_passed = sum(1 for r in anka_results if r.pass_all)
    analysis.anka_total = len(anka_results)
    analysis.python_passed = sum(1 for r in python_results if r.pass_all)
    analysis.python_total = len(python_results)

    # Pass@1 metrics
    if analysis.anka_total > 0:
        pass_rate = compute_pass_at_k(analysis.anka_total, analysis.anka_passed, 1)
        ci = compute_confidence_interval(pass_rate, analysis.anka_total)
        analysis.anka_pass_at_1 = PassAtKResult(
            k=1, pass_rate=pass_rate, ci_lower=ci[0], ci_upper=ci[1]
        )

    if analysis.python_total > 0:
        pass_rate = compute_pass_at_k(analysis.python_total, analysis.python_passed, 1)
        ci = compute_confidence_interval(pass_rate, analysis.python_total)
        analysis.python_pass_at_1 = PassAtKResult(
            k=1, pass_rate=pass_rate, ci_lower=ci[0], ci_upper=ci[1]
        )

    # Category breakdown
    categories: dict[str, dict[str, list[TaskResult]]] = {}
    for result in run.results:
        if result.category not in categories:
            categories[result.category] = {"anka": [], "python": []}
        categories[result.category][result.language].append(result)

    for cat, langs in sorted(categories.items()):
        cat_analysis = CategoryAnalysis(
            category=cat,
            anka_passed=sum(1 for r in langs["anka"] if r.pass_all),
            anka_total=len(langs["anka"]),
            python_passed=sum(1 for r in langs["python"] if r.pass_all),
            python_total=len(langs["python"]),
        )
        analysis.by_category.append(cat_analysis)

    # McNemar's test (paired comparison)
    # Group results by task_id to compare Anka vs Python on same task
    task_results: dict[str, dict[str, bool]] = {}
    for result in run.results:
        if result.task_id not in task_results:
            task_results[result.task_id] = {}
        task_results[result.task_id][result.language] = result.pass_all

    both_pass = 0
    anka_only = 0
    python_only = 0
    both_fail = 0

    for task_id, langs in task_results.items():
        a_pass = langs.get("anka", False)
        p_pass = langs.get("python", False)
        if a_pass and p_pass:
            both_pass += 1
        elif a_pass and not p_pass:
            anka_only += 1
        elif not a_pass and p_pass:
            python_only += 1
        else:
            both_fail += 1

    if both_pass + anka_only + python_only + both_fail > 0:
        analysis.mcnemar = mcnemar_test(both_pass, anka_only, python_only, both_fail)

    # Error classification
    for result in anka_results:
        if not result.pass_all:
            if result.error:
                err_type = classify_error(result.error)
                if err_type == "parse":
                    analysis.anka_errors.parse_errors += 1
                elif err_type == "runtime":
                    analysis.anka_errors.runtime_errors += 1
                elif err_type == "timeout":
                    analysis.anka_errors.timeout_errors += 1
                else:
                    analysis.anka_errors.other_errors += 1
            else:
                analysis.anka_errors.wrong_output += 1

    for result in python_results:
        if not result.pass_all:
            if result.error:
                err_type = classify_error(result.error)
                if err_type == "parse":
                    analysis.python_errors.parse_errors += 1
                elif err_type == "runtime":
                    analysis.python_errors.runtime_errors += 1
                elif err_type == "timeout":
                    analysis.python_errors.timeout_errors += 1
                else:
                    analysis.python_errors.other_errors += 1
            else:
                analysis.python_errors.wrong_output += 1

    return analysis


def load_run(results_file: Path) -> BenchmarkRun:
    """Load a benchmark run from a JSON file.

    Args:
        results_file: Path to the results JSON file.

    Returns:
        BenchmarkRun object.
    """
    with open(results_file) as f:
        data = json.load(f)

    results = [
        TaskResult(
            task_id=r["task_id"],
            category=r["category"],
            language=r["language"],
            model=r["model"],
            generated_code=r["generated_code"],
            test_results=r["test_results"],
            pass_all=r["pass_all"],
            error=r.get("error"),
            latency_ms=r.get("latency_ms", 0.0),
        )
        for r in data["results"]
    ]

    return BenchmarkRun(
        run_id=data["run_id"],
        timestamp=data["timestamp"],
        model=data["model"],
        temperature=data["temperature"],
        results=results,
    )


def print_analysis(analysis: Analysis) -> None:
    """Print analysis results in a readable format.

    Args:
        analysis: Analysis results.
    """
    print("\n" + "=" * 60)
    print("BENCHMARK ANALYSIS")
    print("=" * 60)
    print(f"Run ID: {analysis.run_id}")
    print(f"Model: {analysis.model}")
    print(f"Temperature: {analysis.temperature}")
    print(f"Total Tasks: {analysis.total_tasks}")
    print()

    # Overall results
    print("OVERALL RESULTS")
    print("-" * 40)
    print(
        f"Anka:  {analysis.anka_passed:3}/{analysis.anka_total:3} "
        f"({analysis.anka_rate * 100:5.1f}%)"
    )
    print(
        f"Python: {analysis.python_passed:3}/{analysis.python_total:3} "
        f"({analysis.python_rate * 100:5.1f}%)"
    )

    # Pass@1 with CI
    print("\nPASS@1 (with 95% CI)")
    print("-" * 40)
    if analysis.anka_pass_at_1:
        r = analysis.anka_pass_at_1
        print(
            f"Anka:  {r.pass_rate * 100:5.1f}% "
            f"[{r.ci_lower * 100:5.1f}%, {r.ci_upper * 100:5.1f}%]"
        )
    if analysis.python_pass_at_1:
        r = analysis.python_pass_at_1
        print(
            f"Python: {r.pass_rate * 100:5.1f}% "
            f"[{r.ci_lower * 100:5.1f}%, {r.ci_upper * 100:5.1f}%]"
        )

    # Category breakdown
    if analysis.by_category:
        print("\nBY CATEGORY")
        print("-" * 40)
        for cat in analysis.by_category:
            print(f"\n  {cat.category}:")
            print(
                f"    Anka:  {cat.anka_passed:2}/{cat.anka_total:2} "
                f"({cat.anka_rate * 100:5.1f}%)"
            )
            print(
                f"    Python: {cat.python_passed:2}/{cat.python_total:2} "
                f"({cat.python_rate * 100:5.1f}%)"
            )

    # McNemar's test
    if analysis.mcnemar:
        m = analysis.mcnemar
        print("\nSTATISTICAL COMPARISON (McNemar's Test)")
        print("-" * 40)
        print(f"Both pass:    {m.both_pass:3}")
        print(f"Anka only:   {m.anka_only:3}")
        print(f"Python only:  {m.python_only:3}")
        print(f"Both fail:    {m.both_fail:3}")
        print(f"\nChi-squared:  {m.chi_squared:.3f}")
        print(f"p-value:      {m.p_value:.4f}")
        if m.significant:
            print("Result:       SIGNIFICANT difference (p < 0.05)")
        else:
            print("Result:       No significant difference (p >= 0.05)")

    # Error breakdown
    print("\nERROR BREAKDOWN")
    print("-" * 40)
    print("Anka:")
    print(f"  Parse errors:   {analysis.anka_errors.parse_errors}")
    print(f"  Runtime errors: {analysis.anka_errors.runtime_errors}")
    print(f"  Wrong output:   {analysis.anka_errors.wrong_output}")
    print(f"  Timeouts:       {analysis.anka_errors.timeout_errors}")
    print(f"  Other:          {analysis.anka_errors.other_errors}")
    print("Python:")
    print(f"  Parse errors:   {analysis.python_errors.parse_errors}")
    print(f"  Runtime errors: {analysis.python_errors.runtime_errors}")
    print(f"  Wrong output:   {analysis.python_errors.wrong_output}")
    print(f"  Timeouts:       {analysis.python_errors.timeout_errors}")
    print(f"  Other:          {analysis.python_errors.other_errors}")

    print()


def main() -> int:
    """Run analysis on benchmark results."""
    parser = argparse.ArgumentParser(
        description="Analyze benchmark results",
    )
    parser.add_argument(
        "results_file",
        type=Path,
        help="Path to the results JSON file",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a markdown report",
    )

    args = parser.parse_args()

    if not args.results_file.exists():
        print(f"Error: Results file not found: {args.results_file}")
        return 1

    run = load_run(args.results_file)
    analysis = analyze_run(run)

    if args.report:
        from benchmarks.report import generate_report

        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"report_{analysis.run_id}.md"

        report = generate_report(analysis, output_path)
        print(f"Report saved to: {output_path}")
        print()
        print(report)
    else:
        print_analysis(analysis)

    return 0


if __name__ == "__main__":
    sys.exit(main())
