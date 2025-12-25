"""Report generation for benchmark results.

Generates markdown reports with tables, analysis, and findings.

Usage:
    python -m benchmarks.report results/run_xxx.json
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from benchmarks.analyze import Analysis, analyze_run, load_run


def generate_report(
    analysis: Analysis,
    output_path: Optional[Path] = None,
) -> str:
    """Generate a markdown report from benchmark analysis.

    Args:
        analysis: The analysis results.
        output_path: Optional path to save the report.

    Returns:
        The markdown report as a string.
    """
    lines = []

    # Header
    lines.append("# Anka LLM Benchmark Report")
    lines.append("")
    lines.append(f"**Run ID:** {analysis.run_id}")
    lines.append(f"**Model:** {analysis.model}")
    lines.append(f"**Temperature:** {analysis.temperature}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")

    anka_rate = analysis.anka_rate * 100
    python_rate = analysis.python_rate * 100
    diff = anka_rate - python_rate

    if diff > 5:
        summary = f"Anka outperforms Python by {diff:.1f} percentage points."
    elif diff < -5:
        summary = f"Python outperforms Anka by {-diff:.1f} percentage points."
    else:
        summary = "Anka and Python perform comparably."

    lines.append(summary)
    lines.append("")

    # Summary Table
    lines.append("## Summary Results")
    lines.append("")
    lines.append("| Language | Passed | Total | Pass Rate |")
    lines.append("|----------|--------|-------|-----------|")
    lines.append(
        f"| Anka    | {analysis.anka_passed} | {analysis.anka_total} | "
        f"{anka_rate:.1f}% |"
    )
    lines.append(
        f"| Python   | {analysis.python_passed} | {analysis.python_total} | "
        f"{python_rate:.1f}% |"
    )
    lines.append("")

    # Pass@1 with CI
    lines.append("### Pass@1 with 95% Confidence Intervals")
    lines.append("")
    lines.append("| Language | Pass@1 | 95% CI |")
    lines.append("|----------|--------|--------|")

    if analysis.anka_pass_at_1:
        r = analysis.anka_pass_at_1
        lines.append(
            f"| Anka    | {r.pass_rate * 100:.1f}% | "
            f"[{r.ci_lower * 100:.1f}%, {r.ci_upper * 100:.1f}%] |"
        )
    if analysis.python_pass_at_1:
        r = analysis.python_pass_at_1
        lines.append(
            f"| Python   | {r.pass_rate * 100:.1f}% | "
            f"[{r.ci_lower * 100:.1f}%, {r.ci_upper * 100:.1f}%] |"
        )
    lines.append("")

    # Results by Category
    if analysis.by_category:
        lines.append("## Results by Category")
        lines.append("")
        lines.append("| Category | Anka | Python | Difference |")
        lines.append("|----------|-------|--------|------------|")

        for cat in analysis.by_category:
            anka_str = f"{cat.anka_passed}/{cat.anka_total} ({cat.anka_rate * 100:.0f}%)"
            python_str = f"{cat.python_passed}/{cat.python_total} ({cat.python_rate * 100:.0f}%)"
            diff_val = (cat.anka_rate - cat.python_rate) * 100
            diff_str = f"+{diff_val:.0f}%" if diff_val >= 0 else f"{diff_val:.0f}%"
            lines.append(f"| {cat.category} | {anka_str} | {python_str} | {diff_str} |")

        lines.append("")

    # Statistical Significance
    if analysis.mcnemar:
        m = analysis.mcnemar
        lines.append("## Statistical Significance")
        lines.append("")
        lines.append("Using McNemar's test for paired comparison:")
        lines.append("")
        lines.append("**Contingency Table:**")
        lines.append("")
        lines.append("|                | Python Pass | Python Fail |")
        lines.append("|----------------|-------------|-------------|")
        lines.append(f"| **Anka Pass** | {m.both_pass} | {m.anka_only} |")
        lines.append(f"| **Anka Fail** | {m.python_only} | {m.both_fail} |")
        lines.append("")
        lines.append(f"- **Chi-squared:** {m.chi_squared:.3f}")
        lines.append(f"- **p-value:** {m.p_value:.4f}")
        lines.append("")

        if m.significant:
            lines.append(
                "**Result:** The difference is **statistically significant** (p < 0.05)."
            )
        else:
            lines.append(
                "**Result:** The difference is **not statistically significant** (p >= 0.05)."
            )
        lines.append("")

    # Error Analysis
    lines.append("## Error Analysis")
    lines.append("")
    lines.append("| Error Type | Anka | Python |")
    lines.append("|------------|-------|--------|")
    lines.append(
        f"| Parse errors | {analysis.anka_errors.parse_errors} | "
        f"{analysis.python_errors.parse_errors} |"
    )
    lines.append(
        f"| Runtime errors | {analysis.anka_errors.runtime_errors} | "
        f"{analysis.python_errors.runtime_errors} |"
    )
    lines.append(
        f"| Wrong output | {analysis.anka_errors.wrong_output} | "
        f"{analysis.python_errors.wrong_output} |"
    )
    lines.append(
        f"| Timeouts | {analysis.anka_errors.timeout_errors} | "
        f"{analysis.python_errors.timeout_errors} |"
    )
    lines.append(
        f"| Other | {analysis.anka_errors.other_errors} | "
        f"{analysis.python_errors.other_errors} |"
    )
    lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("### Benchmark Setup")
    lines.append("")
    lines.append(f"- **Model:** {analysis.model}")
    lines.append(f"- **Temperature:** {analysis.temperature}")
    lines.append(f"- **Total Tasks:** {analysis.total_tasks}")
    lines.append("")
    lines.append("### Evaluation Criteria")
    lines.append("")
    lines.append("- Each task has 3 test cases")
    lines.append("- A task is considered passed only if ALL test cases pass")
    lines.append("- Output comparison uses exact matching with floating-point tolerance")
    lines.append("")
    lines.append("### Statistical Methods")
    lines.append("")
    lines.append("- **Pass@1:** Unbiased estimator from the Codex paper")
    lines.append("- **Confidence Intervals:** Wilson score interval (95% CI)")
    lines.append("- **Paired Comparison:** McNemar's test with continuity correction")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by Anka Benchmark Suite*")

    report = "\n".join(lines)

    if output_path:
        output_path.write_text(report)

    return report


def main() -> int:
    """Generate a benchmark report."""
    parser = argparse.ArgumentParser(
        description="Generate benchmark report",
    )
    parser.add_argument(
        "results_file",
        type=Path,
        help="Path to the results JSON file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path for the markdown report",
    )

    args = parser.parse_args()

    if not args.results_file.exists():
        print(f"Error: Results file not found: {args.results_file}")
        return 1

    run = load_run(args.results_file)
    analysis = analyze_run(run)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"report_{analysis.run_id}.md"

    report = generate_report(analysis, output_path)

    print(f"Report saved to: {output_path}")
    print()
    print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
