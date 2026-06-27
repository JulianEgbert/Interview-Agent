from pathlib import Path

from web_app import (
    create_session_payload,
    parse_evaluation_markdown,
    read_evaluation_payload,
)


def test_create_session_payload_dispatches_selected_challenge(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LIVEKIT_URL", "wss://example.livekit.cloud")
    monkeypatch.setenv("LIVEKIT_API_KEY", "devkey")
    monkeypatch.setenv("LIVEKIT_API_SECRET", "devsecret")
    monkeypatch.setenv("INTERVIEWROOM_AGENT_NAME", "interview-room-agent")

    payload = create_session_payload(
        challenge_id="minimum-meeting-rooms",
        participant_name="Demo Candidate",
        workspace_root=tmp_path,
    )

    assert payload["livekitUrl"] == "wss://example.livekit.cloud"
    assert payload["agentName"] == "interview-room-agent"
    assert payload["challenge"]["id"] == "minimum-meeting-rooms"
    assert payload["roomName"].startswith("interviewroom-minimum-meeting-rooms-")
    assert payload["token"]
    assert Path(payload["workspace"]["solutionPath"]).exists()
    assert payload["workspace"]["links"]["solution"].startswith("vscode://file/")
    assert payload["workspace"]["links"]["solution"].endswith("/solution.py:1:1")
    assert payload["workspace"]["links"]["solutionRaw"].endswith("/solution.py")


def test_read_evaluation_payload_reports_missing_report(tmp_path: Path) -> None:
    payload = read_evaluation_payload(
        "minimum-meeting-rooms",
        workspace_root=tmp_path,
    )

    assert payload["available"] is False
    assert payload["challengeId"] == "minimum-meeting-rooms"


def test_parse_evaluation_markdown_returns_scorecard_payload() -> None:
    payload = parse_evaluation_markdown(
        """# InterviewRoom Evaluation: Minimum Meeting Rooms

- Challenge id: `minimum-meeting-rooms`
- Difficulty: `new-grad`
- Type: `coding`
- Candidate file: `candidate_workspace/minimum-meeting-rooms/solution.py`

## Overall Score

[####-] 4/5

## Rubric

| Dimension | Score |
| --- | --- |
| Problem understanding | `[#####] 5/5` |
| Thinking aloud | `[###--] 3/5` |
| Code correctness | `[####-] 4/5` |

## Local Test Result

```text
Passed 4 of 4 local tests.
```

## What Went Well

Clear explanation of the interval approach.

## What To Improve

Talk through edge cases earlier.

## Notable Moments

Asked about back-to-back meetings.

## Recommended Next Steps

Practice heap-based variants.
"""
    )

    assert payload["title"] == "InterviewRoom Evaluation: Minimum Meeting Rooms"
    assert payload["metadata"]["Challenge id"] == "minimum-meeting-rooms"
    assert payload["overallScore"]["score"] == 4
    assert payload["overallScore"]["percent"] == 80
    assert payload["rubric"][1]["label"] == "Thinking aloud"
    assert payload["rubric"][1]["score"] == 3
    assert payload["testResult"] == "Passed 4 of 4 local tests."
    assert "edge cases" in payload["sections"]["whatToImprove"]
