from pathlib import Path

from web_app import create_session_payload


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
