"""Run the Starshot experiment with the Anthropic API."""
import os
import re
import sys

from dotenv import load_dotenv
load_dotenv('.env.txt')

import anthropic

from starshot.experiment.tasks import get_task
from starshot.experiment.runner import ExperimentConfig, run_experiment
from starshot.experiment.results import print_summary


client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])


def generate(prompt, model, temperature):
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        temperature=temperature,
        messages=[{'role': 'user', 'content': prompt}],
    )
    text = resp.content[0].text
    # Extract code block if present
    code_match = re.search(r'```(?:python|scheme|lisp)?\n(.*?)```', text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return text.strip()


def main():
    task_ids = sys.argv[1:] if len(sys.argv) > 1 else ['factorial']
    num_trials = 3

    config = ExperimentConfig(
        model='claude-sonnet-4-5-20250929',
        tasks=task_ids,
        num_trials=num_trials,
        temperature=0.0,
    )

    print(f"Running experiment on {task_ids} ({num_trials} trials each)...")
    print()

    results = run_experiment(config, generate_fn=generate)
    print_summary(results)

    # Show generated code samples
    print()
    print("=== SAMPLE GENERATED CODE ===")
    seen = set()
    for t in results.trials:
        key = (t.task_id, t.group)
        if key in seen:
            continue
        seen.add(key)
        print(f"--- {t.group.upper()} (task={t.task_id}, trial {t.trial}) ---")
        print(t.generated_code[:600])
        if t.eval_result:
            print(f"  Parse: {'OK' if t.eval_result.parse_success else 'FAIL'}")
            print(f"  Compile: {'OK' if t.eval_result.compile_success else 'FAIL'}")
            print(f"  Pass rate: {t.eval_result.pass_rate:.0%}")
            for tr in t.eval_result.test_results:
                status = "PASS" if tr.passed else "FAIL"
                print(f"    {status}: input={tr.test_case.input_args} "
                      f"expected={tr.test_case.expected_output} "
                      f"got={tr.actual_output}"
                      + (f" error={tr.error}" if tr.error else ""))
        print()


if __name__ == '__main__':
    main()
