"""
Tracks optimization progress across iterations.
Stores which tasks pass/fail, what fixes were applied, and improvement over time.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from dataclasses import dataclass, field, asdict


@dataclass
class TaskStatus:
    """Status of a single task across models."""
    task_id: str
    category: str

    # Results by model: {model: {language: pass_rate}}
    results: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Failure info
    common_errors: List[str] = field(default_factory=list)
    fix_attempts: List[str] = field(default_factory=list)

    # Status
    needs_attention: bool = True
    fixed: bool = False

    def anka_pass_rate(self, model: str) -> float:
        return self.results.get(model, {}).get('anka', 0.0)

    def python_pass_rate(self, model: str) -> float:
        return self.results.get(model, {}).get('python', 0.0)

    def is_task_bug(self, model: str) -> bool:
        """Both languages fail = likely task definition bug."""
        return self.anka_pass_rate(model) < 0.5 and self.python_pass_rate(model) < 0.5


@dataclass
class OptimizationIteration:
    """Record of a single optimization iteration."""
    iteration: int
    timestamp: str
    model: str

    # What was tested
    tasks_tested: List[str]
    samples_per_task: int

    # Results
    anka_pass_rate: float
    python_pass_rate: float
    anka_parse_rate: float

    # Changes made this iteration
    fixes_applied: List[str] = field(default_factory=list)

    # Improvement
    improvement_from_last: float = 0.0


@dataclass
class OptimizationState:
    """Full optimization state - persisted to disk."""

    # Metadata
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    # Models being tested
    models: List[str] = field(default_factory=list)

    # Task statuses
    tasks: Dict[str, TaskStatus] = field(default_factory=dict)

    # Iteration history
    iterations: List[OptimizationIteration] = field(default_factory=list)

    # Current best results by model
    best_results: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Tasks that still need work
    @property
    def failing_tasks(self) -> Set[str]:
        return {tid for tid, t in self.tasks.items() if t.needs_attention}

    @property
    def fixed_tasks(self) -> Set[str]:
        return {tid for tid, t in self.tasks.items() if t.fixed}

    def get_tasks_to_test(self, model: str) -> List[str]:
        """Get tasks that need testing for this model."""
        tasks_to_test = []
        for tid, task in self.tasks.items():
            # Test if never tested on this model
            if model not in task.results:
                tasks_to_test.append(tid)
            # Test if previously failed on this model
            elif task.anka_pass_rate(model) < 1.0:
                tasks_to_test.append(tid)
        return tasks_to_test

    def update_task(self, task_id: str, model: str, anka_rate: float, python_rate: float, errors: List[str] = None):
        """Update task status with new results."""
        if task_id not in self.tasks:
            category = task_id.rsplit('_', 1)[0]
            self.tasks[task_id] = TaskStatus(task_id=task_id, category=category)

        task = self.tasks[task_id]
        if model not in task.results:
            task.results[model] = {}

        task.results[model]['anka'] = anka_rate
        task.results[model]['python'] = python_rate

        if errors:
            task.common_errors = list(set(task.common_errors + errors))

        # Update status
        task.needs_attention = anka_rate < 0.9  # Below 90% needs work
        task.fixed = anka_rate >= 0.9

        self.last_updated = datetime.now().isoformat()

    def add_iteration(self, iteration: OptimizationIteration):
        """Add a new iteration record."""
        # Calculate improvement
        if self.iterations:
            last = self.iterations[-1]
            iteration.improvement_from_last = iteration.anka_pass_rate - last.anka_pass_rate

        self.iterations.append(iteration)
        self.last_updated = datetime.now().isoformat()

    def save(self, path: str = 'benchmarks/optimization_state.json'):
        """Save state to disk."""
        Path(path).parent.mkdir(exist_ok=True)

        # Convert to serializable dict
        data = {
            'created': self.created,
            'last_updated': self.last_updated,
            'models': self.models,
            'tasks': {tid: asdict(t) for tid, t in self.tasks.items()},
            'iterations': [asdict(i) for i in self.iterations],
            'best_results': self.best_results
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str = 'benchmarks/optimization_state.json') -> 'OptimizationState':
        """Load state from disk."""
        if not Path(path).exists():
            return cls()

        with open(path) as f:
            data = json.load(f)

        state = cls()
        state.created = data.get('created', state.created)
        state.last_updated = data.get('last_updated', state.last_updated)
        state.models = data.get('models', [])
        state.best_results = data.get('best_results', {})

        # Reconstruct tasks
        for tid, tdata in data.get('tasks', {}).items():
            state.tasks[tid] = TaskStatus(**tdata)

        # Reconstruct iterations
        for idata in data.get('iterations', []):
            state.iterations.append(OptimizationIteration(**idata))

        return state

    def print_summary(self):
        """Print current optimization status."""
        print("\n" + "="*70)
        print("OPTIMIZATION STATUS")
        print("="*70)

        print(f"\nIterations completed: {len(self.iterations)}")
        print(f"Tasks tracked: {len(self.tasks)}")
        print(f"Tasks needing attention: {len(self.failing_tasks)}")
        print(f"Tasks fixed: {len(self.fixed_tasks)}")

        if self.iterations:
            latest = self.iterations[-1]
            print(f"\nLatest results ({latest.model}):")
            print(f"  Anka pass rate: {latest.anka_pass_rate*100:.1f}%")
            print(f"  Python pass rate: {latest.python_pass_rate*100:.1f}%")
            print(f"  Anka parse rate: {latest.anka_parse_rate*100:.1f}%")

        # By category
        categories: Dict[str, Dict[str, int]] = {}
        for task in self.tasks.values():
            if task.category not in categories:
                categories[task.category] = {'total': 0, 'fixed': 0}
            categories[task.category]['total'] += 1
            if task.fixed:
                categories[task.category]['fixed'] += 1

        print(f"\nBy category:")
        for cat, stats in sorted(categories.items()):
            pct = stats['fixed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {cat}: {stats['fixed']}/{stats['total']} fixed ({pct:.0f}%)")

        # Failing tasks
        if self.failing_tasks:
            print(f"\nTasks needing attention:")
            for tid in sorted(self.failing_tasks)[:10]:
                task = self.tasks[tid]
                rates = [f"{m}: {task.anka_pass_rate(m)*100:.0f}%" for m in task.results.keys()]
                print(f"  {tid}: {', '.join(rates)}")
            if len(self.failing_tasks) > 10:
                print(f"  ... and {len(self.failing_tasks) - 10} more")
