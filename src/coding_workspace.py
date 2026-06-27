import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from challenges import CodingSpec, InterviewChallenge, get_coding_spec

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_ROOT = PROJECT_ROOT / "candidate_workspace"

RUNNER_CODE = r"""
import importlib.util
import json
import sys
import traceback


def normalize(value):
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(val) for key, val in value.items()}
    return value


def main():
    payload = json.load(sys.stdin)
    result = {
        "ok": True,
        "passed": 0,
        "total": len(payload["test_cases"]),
        "results": [],
    }

    try:
        spec = importlib.util.spec_from_file_location(
            "candidate_solution",
            payload["solution_path"],
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        candidate_fn = getattr(module, payload["function_name"])
    except Exception:
        result["ok"] = False
        result["error"] = traceback.format_exc(limit=4)
        print(json.dumps(result))
        return

    for case in payload["test_cases"]:
        case_result = {
            "name": case["name"],
            "passed": False,
            "expected": case["expected"],
        }
        try:
            actual = candidate_fn(*case.get("args", []), **case.get("kwargs", {}))
            normalized_actual = normalize(actual)
            case_result["actual"] = normalized_actual
            case_result["passed"] = normalized_actual == normalize(case["expected"])
        except Exception:
            case_result["error"] = traceback.format_exc(limit=4)

        if case_result["passed"]:
            result["passed"] += 1
        result["results"].append(case_result)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
"""


@dataclass(frozen=True)
class CandidateWorkspace:
    challenge: InterviewChallenge
    coding_spec: CodingSpec | None
    directory: Path
    solution_path: Path | None
    readme_path: Path

    @property
    def has_runnable_tests(self) -> bool:
        return self.coding_spec is not None and self.solution_path is not None


def _workspace_root(workspace_root: Path | None = None) -> Path:
    if workspace_root is not None:
        return workspace_root

    configured_root = os.getenv("INTERVIEWROOM_WORKSPACE_DIR")
    if configured_root:
        path = Path(configured_root)
        return path if path.is_absolute() else PROJECT_ROOT / path

    return DEFAULT_WORKSPACE_ROOT


def _workspace_readme(challenge: InterviewChallenge, spec: CodingSpec | None) -> str:
    lines = [
        f"# {challenge.title}",
        "",
        challenge.prompt,
        "",
        "## Examples",
        *[f"- {example}" for example in challenge.examples],
        "",
        "## Constraints",
        *[f"- {constraint}" for constraint in challenge.constraints],
    ]

    if spec is not None:
        lines.extend(
            [
                "",
                "## Local Coding Task",
                "",
                f"Edit `solution.py` and implement `{spec.function_name}`.",
                "The InterviewRoom agent can inspect this file and run the local tests when you ask.",
            ]
        )

    return "\n".join(lines) + "\n"


def prepare_candidate_workspace(
    challenge: InterviewChallenge,
    *,
    reset: bool = False,
    workspace_root: Path | None = None,
) -> CandidateWorkspace:
    spec = get_coding_spec(challenge.id)
    directory = _workspace_root(workspace_root) / challenge.id
    directory.mkdir(parents=True, exist_ok=True)

    readme_path = directory / "README.md"
    readme_path.write_text(_workspace_readme(challenge, spec), encoding="utf-8")

    solution_path = None
    if spec is not None:
        solution_path = directory / "solution.py"
        if reset or not solution_path.exists():
            solution_path.write_text(spec.starter_code, encoding="utf-8")

    return CandidateWorkspace(
        challenge=challenge,
        coding_spec=spec,
        directory=directory,
        solution_path=solution_path,
        readme_path=readme_path,
    )


def read_candidate_code(workspace: CandidateWorkspace, *, max_chars: int = 6000) -> str:
    if workspace.solution_path is None:
        return "This challenge does not have a local Python coding workspace."
    if not workspace.solution_path.exists():
        return f"No solution file exists at {workspace.solution_path}."

    code = workspace.solution_path.read_text(encoding="utf-8")
    if len(code) > max_chars:
        code = f"{code[:max_chars]}\n\n... truncated ..."

    return f"Current candidate file: {workspace.solution_path}\n\n{code}"


def run_candidate_tests(workspace: CandidateWorkspace) -> str:
    if workspace.coding_spec is None or workspace.solution_path is None:
        return "This challenge does not have runnable local tests."
    if not workspace.solution_path.exists():
        return f"No solution file exists at {workspace.solution_path}."

    spec = workspace.coding_spec
    payload = {
        "solution_path": str(workspace.solution_path),
        "function_name": spec.function_name,
        "test_cases": [case.model_dump() for case in spec.test_cases],
    }

    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-c", RUNNER_CODE],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (
            f"Local tests timed out after {spec.timeout_seconds:.1f} seconds. "
            "The candidate solution may have an infinite loop or slow path."
        )

    if completed.returncode != 0:
        return (
            "The test runner failed before it could evaluate the solution.\n"
            f"stderr:\n{completed.stderr.strip()}"
        )

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return (
            "The test runner returned output that was not valid JSON.\n"
            f"stdout:\n{completed.stdout.strip()}\n"
            f"stderr:\n{completed.stderr.strip()}"
        )

    return format_test_result(result)


def format_test_result(result: dict[str, Any]) -> str:
    if not result.get("ok", False):
        return (
            "The candidate solution could not be loaded.\n"
            f"{result.get('error', 'No error details were provided.')}"
        )

    lines = [f"Passed {result['passed']} of {result['total']} local tests."]
    for case in result["results"]:
        if case["passed"]:
            lines.append(f"- PASS: {case['name']}")
            continue

        lines.append(f"- FAIL: {case['name']}")
        if "error" in case:
            lines.append(f"  Error: {case['error'].strip()}")
        else:
            lines.append(f"  Expected: {case['expected']}")
            lines.append(f"  Actual: {case.get('actual')}")

    return "\n".join(lines)
