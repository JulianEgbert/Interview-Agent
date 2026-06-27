from interview import DEFAULT_CHALLENGE, OPENING_MESSAGE, build_interviewer_instructions


def test_opening_message_starts_mvp_interview() -> None:
    assert "thirty-five minutes" in OPENING_MESSAGE
    assert "minimum number of meeting rooms" in OPENING_MESSAGE
    assert "clarifying questions" in OPENING_MESSAGE


def test_default_challenge_has_interview_material() -> None:
    assert DEFAULT_CHALLENGE.title == "Minimum Meeting Rooms"
    assert len(DEFAULT_CHALLENGE.examples) >= 2
    assert len(DEFAULT_CHALLENGE.hints) == 3
    assert "Back-to-back events do not overlap." in DEFAULT_CHALLENGE.constraints


def test_interviewer_instructions_keep_candidate_driving() -> None:
    instructions = build_interviewer_instructions()

    assert "Ask one question at a time." in instructions
    assert "Do not provide the final algorithm or full solution" in instructions
    assert "This prototype does not analyze screen pixels directly." in instructions
    assert "time and space complexity" in instructions
