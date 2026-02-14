"""Results analysis and reporting for the Starshot experiment."""
from __future__ import annotations
from .runner import ExperimentResults


def print_summary(results: ExperimentResults):
    """Print a human-readable summary of experiment results."""
    summary = results.summary()
    print("=" * 60)
    print("STARSHOT EXPERIMENT RESULTS")
    print("=" * 60)
    print(f"Tasks: {summary['total_tasks']}")
    print(f"Total trials: {summary['total_trials']}")
    print()

    print("CONTROL GROUP (Plain Python)")
    print("-" * 40)
    c = summary['control']
    print(f"  Trials: {c['count']}")
    print(f"  Average pass rate: {c['pass_rate']:.1%}")
    print(f"  Fully correct: {c['all_passed']}/{c['count']}")
    print()

    print("TEST GROUP (Starshot IR)")
    print("-" * 40)
    t = summary['test']
    print(f"  Trials: {t['count']}")
    print(f"  Average pass rate: {t['pass_rate']:.1%}")
    print(f"  Fully correct: {t['all_passed']}/{t['count']}")
    print(f"  Parse failures: {t['parse_failures']}")
    print(f"  Compile failures: {t['compile_failures']}")
    print()

    # Per-task breakdown
    print("PER-TASK BREAKDOWN")
    print("-" * 60)
    print(f"{'Task':<25} {'Control':>10} {'IR':>10} {'Delta':>10}")
    print("-" * 60)

    task_ids = sorted(set(t.task_id for t in results.trials))
    for task_id in task_ids:
        control_trials = [t for t in results.trials
                          if t.task_id == task_id and t.group == "control" and t.eval_result]
        test_trials = [t for t in results.trials
                       if t.task_id == task_id and t.group == "test" and t.eval_result]

        c_rate = (sum(t.eval_result.pass_rate for t in control_trials) / len(control_trials)
                  if control_trials else 0)
        t_rate = (sum(t.eval_result.pass_rate for t in test_trials) / len(test_trials)
                  if test_trials else 0)
        delta = t_rate - c_rate

        print(f"{task_id:<25} {c_rate:>9.0%} {t_rate:>9.0%} {delta:>+9.0%}")

    print("=" * 60)
