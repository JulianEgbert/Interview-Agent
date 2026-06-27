from pathlib import Path

from challenges import get_challenge
from coding_workspace import (
    EVALUATION_TEMPLATE_PATH,
    prepare_candidate_workspace,
    read_candidate_code,
    run_candidate_tests,
    write_evaluation_report,
)


def test_prepare_candidate_workspace_creates_starter(tmp_path: Path) -> None:
    challenge = get_challenge("minimum-meeting-rooms")

    workspace = prepare_candidate_workspace(challenge, workspace_root=tmp_path)

    assert workspace.solution_path is not None
    assert workspace.solution_path.exists()
    assert "def min_meeting_rooms" in workspace.solution_path.read_text()
    assert workspace.readme_path.exists()


def test_prepare_candidate_workspace_preserves_existing_solution(
    tmp_path: Path,
) -> None:
    challenge = get_challenge("minimum-meeting-rooms")
    workspace = prepare_candidate_workspace(challenge, workspace_root=tmp_path)
    assert workspace.solution_path is not None
    workspace.solution_path.write_text(
        "def min_meeting_rooms(events):\n    return 123\n"
    )

    prepare_candidate_workspace(challenge, workspace_root=tmp_path)

    assert "return 123" in workspace.solution_path.read_text()


def test_run_candidate_tests_reports_failing_starter(tmp_path: Path) -> None:
    challenge = get_challenge("minimum-meeting-rooms")
    workspace = prepare_candidate_workspace(challenge, workspace_root=tmp_path)

    result = run_candidate_tests(workspace)

    assert "Passed 1 of 4 local tests." in result
    assert "FAIL: overlapping meetings need two rooms" in result


def test_run_candidate_tests_reports_passing_solution(tmp_path: Path) -> None:
    challenge = get_challenge("first-unique-visitor")
    workspace = prepare_candidate_workspace(challenge, workspace_root=tmp_path)
    assert workspace.solution_path is not None
    workspace.solution_path.write_text(
        "def first_unique_visitor(visitors):\n"
        "    counts = {}\n"
        "    for visitor in visitors:\n"
        "        counts[visitor] = counts.get(visitor, 0) + 1\n"
        "    for visitor in visitors:\n"
        "        if counts[visitor] == 1:\n"
        "            return visitor\n"
        "    return None\n"
    )

    result = run_candidate_tests(workspace)

    assert "Passed 4 of 4 local tests." in result
    assert "FAIL" not in result


def test_read_candidate_code_includes_solution_path(tmp_path: Path) -> None:
    challenge = get_challenge("minimum-meeting-rooms")
    workspace = prepare_candidate_workspace(challenge, workspace_root=tmp_path)

    code_context = read_candidate_code(workspace)

    assert str(workspace.solution_path) in code_context
    assert "def min_meeting_rooms" in code_context


def test_write_evaluation_report_creates_markdown_scorecard(tmp_path: Path) -> None:
    challenge = get_challenge("first-unique-visitor")
    workspace = prepare_candidate_workspace(challenge, workspace_root=tmp_path)

    message = write_evaluation_report(
        workspace,
        overall_score=4,
        problem_understanding=5,
        communication=4,
        thinking_aloud=3,
        algorithmic_reasoning=4,
        code_correctness=3,
        edge_case_handling=4,
        testing_approach=3,
        complexity_discussion=4,
        strengths="Clear reasoning and good use of counting.",
        improvements="Add a final pass over the original order.",
        next_steps="Practice streaming variants.",
        transcript_moments="Asked about empty input before coding.",
    )

    report = workspace.evaluation_path.read_text(encoding="utf-8")

    assert str(workspace.evaluation_path) in message
    assert "# InterviewRoom Evaluation: First Unique Visitor" in report
    assert "[####-] 4/5" in report
    assert "| Problem understanding | `[#####] 5/5` |" in report
    assert "| Thinking aloud | `[###--] 3/5` |" in report
    assert "## Local Test Result" in report
    assert "Clear reasoning" in report


def test_evaluation_template_uses_named_format_placeholders() -> None:
    template = EVALUATION_TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "{challenge_title}" in template
    assert "{rubric_rows}" in template
    assert "{test_result}" in template
