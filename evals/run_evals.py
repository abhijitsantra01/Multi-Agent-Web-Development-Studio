"""
Runner script for LangSmith agent evaluation suite.
Executes automated benchmarks and logs scores to the LangSmith evaluation dashboard.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv(override=True)

import orchestrator
import project_store
from evals.evaluators import (
    files_completeness_evaluator,
    syntax_validity_evaluator,
    latency_benchmark_evaluator
)

BENCHMARK_EXAMPLES = [
    {
        "inputs": {"prompt": "Design a high-speed telemetry monitoring dashboard with real-time charts and dark mode."},
        "outputs": {"expected_files": ["index.html", "styles.css", "app.js"]}
    },
    {
        "inputs": {"prompt": "Create an interactive personal finance portfolio tracker with asset allocation cards and an add-transaction modal."},
        "outputs": {"expected_files": ["index.html", "styles.css", "app.js"]}
    }
]

def target_pipeline(inputs: dict) -> dict:
    """Invokes the multi-agent initial synthesis pipeline for evaluation."""
    prompt = inputs["prompt"]
    meta = project_store.create_new_project(prompt=prompt)
    pid = meta["id"]
    
    return orchestrator.synthesize_initial_project(
        project_id=pid,
        prompt=prompt,
        complex_model=orchestrator.DEFAULT_COMPLEX_MODEL,
        lite_model=orchestrator.DEFAULT_LITE_MODEL
    )

def run():
    from langsmith import evaluate, Client
    client = Client()
    
    dataset_name = "gemini-orchestrator-benchmarks"
    if not client.has_dataset(dataset_name=dataset_name):
        print(f"Creating evaluation dataset '{dataset_name}'...")
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Benchmark dataset for multi-agent web synthesis"
        )
        for ex in BENCHMARK_EXAMPLES:
            client.create_example(inputs=ex["inputs"], outputs=ex["outputs"], dataset_id=dataset.id)
    else:
        print(f"Using existing dataset '{dataset_name}'.")

    print("Running LangSmith multi-agent evaluation suite...")
    results = evaluate(
        target_pipeline,
        data=dataset_name,
        evaluators=[
            files_completeness_evaluator,
            syntax_validity_evaluator,
            latency_benchmark_evaluator
        ],
        experiment_prefix="orchestrator-eval",
        metadata={
            "complex_model": orchestrator.DEFAULT_COMPLEX_MODEL,
            "lite_model": orchestrator.DEFAULT_LITE_MODEL,
            "workers_concurrency": 4,
            "assembler_thinking_budget": 0
        }
    )
    print("\n✓ Evaluation run complete! View live benchmark comparison in your LangSmith dashboard.")
    return results

if __name__ == "__main__":
    run()
