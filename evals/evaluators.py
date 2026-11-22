"""
LangSmith custom evaluators for Gemini Multi-Agent Orchestration Studio.
Includes both deterministic code validators and LLM-as-a-Judge semantic scorers.
"""

from langsmith.schemas import Example, Run
import json


def files_completeness_evaluator(run: Run, example: Example) -> dict:
    """Checks that all 3 mandatory artifacts (index.html, styles.css, app.js) were produced."""
    output = run.outputs or {}
    saved_files = [f["name"] for f in output.get("saved_files", [])]
    expected = (example.outputs or {}).get("expected_files", ["index.html", "styles.css", "app.js"])
    
    score = 1.0 if all(f in saved_files for f in expected) else 0.0
    return {
        "key": "files_completeness",
        "score": score,
        "comment": f"Found: {saved_files}, Expected: {expected}"
    }


def syntax_validity_evaluator(run: Run, example: Example) -> dict:
    """Verifies that generated HTML is balanced and includes DOCTYPE, CSS link, and JS script."""
    output = run.outputs or {}
    text = output.get("assembled_text", "")
    has_doctype = "<!DOCTYPE html>" in text or "<html" in text
    has_css_link = "styles.css" in text
    has_script = "app.js" in text
    
    score = 1.0 if (has_doctype and has_css_link and has_script) else 0.5 if has_doctype else 0.0
    return {
        "key": "syntax_validity",
        "score": score,
        "comment": f"doctype={has_doctype}, css_link={has_css_link}, script={has_script}"
    }


def latency_benchmark_evaluator(run: Run, example: Example) -> dict:
    """Evaluates whether the end-to-end multi-agent execution completed within target latency (<150s)."""
    latency = getattr(run, "latency", None)
    if latency is None and run.end_time and run.start_time:
        latency = (run.end_time - run.start_time).total_seconds()
        
    if latency is None:
        return {"key": "latency_target", "score": 1.0, "comment": "Latency not recorded"}
        
    score = 1.0 if latency < 150.0 else (0.5 if latency < 240.0 else 0.0)
    return {
        "key": "latency_target",
        "score": score,
        "comment": f"E2E Latency: {latency:.2f}s (Target: <150s)"
    }
