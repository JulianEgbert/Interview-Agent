from challenges import DEFAULT_CHALLENGE
from interview import build_interviewer_instructions, build_opening_message


def test_opening_message_starts_mvp_interview() -> None:
    opening_message = build_opening_message(
        DEFAULT_CHALLENGE,
        workspace_path="candidate_workspace/minimum-meeting-rooms/solution.py",
    )

    assert "thirty-five minutes" in opening_message
    assert "minimum number of meeting rooms" in opening_message
    assert "candidate_workspace/minimum-meeting-rooms/solution.py" in opening_message
    assert "clarifying questions" in opening_message


def test_default_challenge_has_interview_material() -> None:
    assert DEFAULT_CHALLENGE.title == "Minimum Meeting Rooms"
    assert len(DEFAULT_CHALLENGE.examples) >= 2
    assert len(DEFAULT_CHALLENGE.hints) == 3
    assert "Back-to-back events do not overlap." in DEFAULT_CHALLENGE.constraints


def test_interviewer_instructions_keep_candidate_driving() -> None:
    instructions = build_interviewer_instructions(
        workspace_path="candidate_workspace/minimum-meeting-rooms/solution.py",
        function_name="min_meeting_rooms",
        has_runnable_tests=True,
    )

    assert "Ask one question at a time." in instructions
    assert "Do not provide the final algorithm or full solution" in instructions
    assert "This prototype does not analyze screen pixels directly." in instructions
    assert "time and space complexity" in instructions
    assert "Challenge id: minimum-meeting-rooms" in instructions
    assert "implement min_meeting_rooms" in instructions
