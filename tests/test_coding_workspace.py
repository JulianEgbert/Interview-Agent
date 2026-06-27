from pathlib import Path

from challenges import get_challenge
from coding_workspace import (
    prepare_candidate_workspace,
    read_candidate_code,
    run_candidate_tests,
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
