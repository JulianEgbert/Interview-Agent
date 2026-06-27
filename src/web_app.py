import json
import mimetypes
import os
import re
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

from dotenv import load_dotenv
from livekit import api

from challenges import get_challenge, get_coding_spec, load_challenges, select_challenge
from coding_workspace import (
    CandidateWorkspace,
    get_workspace_root,
    prepare_candidate_workspace,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env.local")

WEB_STATIC_DIR = Path(__file__).with_name("web_static")
DEFAULT_HOST = os.getenv("INTERVIEWROOM_WEB_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("INTERVIEWROOM_WEB_PORT", "8765"))
AGENT_NAME = os.getenv("INTERVIEWROOM_AGENT_NAME", "interview-room-agent")
WORKSPACE_FILENAMES = {"README.md", "solution.py", "evaluation.md"}
SCORE_BAR_PATTERN = re.compile(
    r"\[(?P<marks>[#-]+)\]\s+(?P<score>\d+)/(?P<maximum>\d+)"
)
SECTION_PATTERN = re.compile(
    r"^## (?P<title>.+?)\n(?P<body>.*?)(?=^## |\Z)", re.S | re.M
)
METADATA_PATTERN = re.compile(r"^- (?P<label>[^:]+): `(?P<value>.*)`$")
RUBRIC_ROW_PATTERN = re.compile(
    r"^\|\s*(?P<label>[^|]+?)\s*\|\s*`?(?P<score>\[[#-]+\]\s+\d+/\d+)`?\s*\|$"
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower() or "guest"


def _env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} must be set in .env.local")
    return value


def _challenge_summary(challenge_id: str) -> dict[str, Any]:
    challenge = get_challenge(challenge_id)
    coding_spec = get_coding_spec(challenge.id)
    return {
        "id": challenge.id,
        "title": challenge.title,
        "type": challenge.challenge_type,
        "difficulty": challenge.difficulty,
        "categories": list(challenge.categories),
        "tags": list(challenge.tags),
        "prompt": challenge.prompt,
        "examples": list(challenge.examples),
        "constraints": list(challenge.constraints),
        "hasCodingWorkspace": coding_spec is not None,
        "functionName": coding_spec.function_name if coding_spec else None,
    }


def _vscode_file_url(path: Path | None) -> str | None:
    if path is None:
        return None

    encoded_path = quote(str(path.resolve()), safe="/:")
    return f"vscode://file{encoded_path}:1:1"


def _workspace_links(workspace: CandidateWorkspace) -> dict[str, str | None]:
    base = f"/workspace/{workspace.challenge.id}"
    return {
        "readme": f"{base}/README.md",
        "solution": _vscode_file_url(workspace.solution_path),
        "solutionRaw": f"{base}/solution.py" if workspace.solution_path else None,
        "evaluation": f"{base}/evaluation.md",
    }


def _workspace_file_path(
    challenge_id: str,
    filename: str,
    *,
    workspace_root: Path | None = None,
) -> Path:
    if filename not in WORKSPACE_FILENAMES:
        raise ValueError(f"Unsupported workspace file: {filename}")

    get_challenge(challenge_id)
    root = get_workspace_root(workspace_root).resolve()
    path = (root / challenge_id / filename).resolve()
    if root not in path.parents:
        raise ValueError("Workspace file path is outside the workspace root")
    return path


def _score_payload(score_text: str) -> dict[str, Any]:
    cleaned = score_text.strip().strip("`")
    match = SCORE_BAR_PATTERN.search(cleaned)
    if not match:
        return {
            "scoreLabel": cleaned,
            "score": None,
            "maximum": None,
            "percent": 0,
        }

    score = int(match.group("score"))
    maximum = int(match.group("maximum"))
    return {
        "scoreLabel": cleaned,
        "score": score,
        "maximum": maximum,
        "percent": round((score / maximum) * 100) if maximum else 0,
    }


def _strip_code_fence(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_evaluation_markdown(markdown: str) -> dict[str, Any]:
    title = "InterviewRoom Evaluation"
    metadata: dict[str, str] = {}
    sections: dict[str, str] = {}

    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line.removeprefix("# ").strip()
            continue

        metadata_match = METADATA_PATTERN.match(line)
        if metadata_match:
            metadata[metadata_match.group("label")] = metadata_match.group("value")

    for section_match in SECTION_PATTERN.finditer(markdown):
        sections[section_match.group("title").strip()] = section_match.group(
            "body"
        ).strip()

    rubric = []
    for line in sections.get("Rubric", "").splitlines():
        row_match = RUBRIC_ROW_PATTERN.match(line.strip())
        if not row_match:
            continue
        label = row_match.group("label").strip()
        if label in {"Dimension", "---"}:
            continue
        rubric.append(
            {
                "label": label,
                **_score_payload(row_match.group("score")),
            }
        )

    return {
        "title": title,
        "metadata": metadata,
        "overallScore": _score_payload(sections.get("Overall Score", "")),
        "rubric": rubric,
        "testResult": _strip_code_fence(sections.get("Local Test Result", "")),
        "sections": {
            "whatWentWell": sections.get("What Went Well", "").strip(),
            "whatToImprove": sections.get("What To Improve", "").strip(),
            "notableMoments": sections.get("Notable Moments", "").strip(),
            "recommendedNextSteps": sections.get("Recommended Next Steps", "").strip(),
        },
    }


def read_evaluation_payload(
    challenge_id: str,
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    path = _workspace_file_path(
        challenge_id,
        "evaluation.md",
        workspace_root=workspace_root,
    )
    if not path.exists():
        return {
            "available": False,
            "challengeId": challenge_id,
            "message": "No evaluation report has been written yet.",
        }

    return {
        "available": True,
        "challengeId": challenge_id,
        "path": str(path),
        **parse_evaluation_markdown(path.read_text(encoding="utf-8")),
    }


def create_session_payload(
    *,
    challenge_id: str | None,
    participant_name: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    livekit_url = _env_required("LIVEKIT_URL")
    api_key = _env_required("LIVEKIT_API_KEY")
    api_secret = _env_required("LIVEKIT_API_SECRET")

    challenge = get_challenge(challenge_id) if challenge_id else select_challenge()
    workspace = prepare_candidate_workspace(challenge, workspace_root=workspace_root)
    safe_name = participant_name.strip() or "Candidate"
    identity = f"{_slug(safe_name)}-{secrets.token_hex(3)}"
    room_name = f"interviewroom-{challenge.id}-{secrets.token_hex(4)}"
    metadata = json.dumps({"challenge_id": challenge.id})

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(safe_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            api.RoomConfiguration(
                agents=[
                    api.RoomAgentDispatch(
                        agent_name=AGENT_NAME,
                        metadata=metadata,
                    )
                ],
            )
        )
        .to_jwt()
    )

    return {
        "livekitUrl": livekit_url,
        "token": token,
        "roomName": room_name,
        "participantName": safe_name,
        "participantIdentity": identity,
        "agentName": AGENT_NAME,
        "challenge": _challenge_summary(challenge.id),
        "workspace": {
            "directory": str(workspace.directory),
            "solutionPath": str(workspace.solution_path)
            if workspace.solution_path
            else None,
            "evaluationPath": str(workspace.evaluation_path),
            "links": _workspace_links(workspace),
        },
    }


def _json_response(
    handler: BaseHTTPRequestHandler, payload: Any, status: int = 200
) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(
    handler: BaseHTTPRequestHandler,
    body: str,
    *,
    status: int = 200,
    content_type: str = "text/plain; charset=utf-8",
) -> None:
    encoded = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


class InterviewRoomHandler(BaseHTTPRequestHandler):
    server_version = "InterviewRoomWeb/0.1"

    def log_message(self, message_format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {message_format % args}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            return self._serve_static("index.html")
        if path == "/api/challenges":
            return _json_response(
                self,
                {
                    "challenges": [
                        _challenge_summary(challenge.id)
                        for challenge in load_challenges()
                    ]
                },
            )
        if path.startswith("/api/evaluation/"):
            return self._serve_evaluation(path)
        if path.startswith("/workspace/"):
            return self._serve_workspace_file(path)
        if path in {"/app.js", "/styles.css"}:
            return self._serve_static(path.lstrip("/"))
        if path.startswith("/api/"):
            return _json_response(
                self,
                {"error": "Not found"},
                status=HTTPStatus.NOT_FOUND,
            )

        _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/session":
            if path.startswith("/api/"):
                return _json_response(
                    self,
                    {"error": "Not found"},
                    status=HTTPStatus.NOT_FOUND,
                )
            return _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            response = create_session_payload(
                challenge_id=payload.get("challengeId") or None,
                participant_name=payload.get("participantName") or "Candidate",
            )
        except Exception as exc:
            return _json_response(
                self,
                {"error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )

        _json_response(self, response)

    def _serve_static(self, relative_path: str) -> None:
        path = WEB_STATIC_DIR / relative_path
        if not path.exists() or not path.is_file():
            return _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_evaluation(self, request_path: str) -> None:
        parts = [unquote(part) for part in request_path.strip("/").split("/")]
        if len(parts) != 3:
            return _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        try:
            payload = read_evaluation_payload(parts[2])
        except ValueError:
            return _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        _json_response(self, payload)

    def _serve_workspace_file(self, request_path: str) -> None:
        parts = [unquote(part) for part in request_path.strip("/").split("/")]
        if len(parts) != 3 or parts[0] != "workspace":
            return _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        challenge_id, filename = parts[1], parts[2]
        try:
            path = _workspace_file_path(challenge_id, filename)
        except ValueError:
            return _text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        if not path.exists() or not path.is_file():
            return _text_response(
                self,
                f"{filename} does not exist yet.",
                status=HTTPStatus.NOT_FOUND,
            )

        content_type = (
            "text/markdown; charset=utf-8"
            if filename.endswith(".md")
            else "text/plain; charset=utf-8"
        )
        _text_response(
            self, path.read_text(encoding="utf-8"), content_type=content_type
        )


def main() -> None:
    host = os.getenv("INTERVIEWROOM_WEB_HOST", DEFAULT_HOST)
    port = int(os.getenv("INTERVIEWROOM_WEB_PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((host, port), InterviewRoomHandler)
    url_host = "localhost" if host in {"0.0.0.0", "::"} else host
    print(f"InterviewRoom web app running at http://{url_host}:{port}")
    print("Run the agent in another terminal with: uv run python src/agent.py dev")
    server.serve_forever()


if __name__ == "__main__":
    main()
