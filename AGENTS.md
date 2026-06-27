# AGENTS.md

This is an InterviewRoom prototype built on the LiveKit Agents Python starter.

Use `uv` for dependency management, running the agent, formatting, and tests.
The runtime entrypoint is `src/agent.py`. Interview product behavior is kept in
`src/interview.py` so prompt/challenge iteration stays easy during the hackathon.

Useful commands:

```bash
uv sync
uv run python src/agent.py console
uv run python src/agent.py dev
uv run pytest
uv run ruff format
uv run ruff check
```

LiveKit Agents changes quickly. Prefer `lk docs`, the LiveKit docs MCP server,
or the official LiveKit documentation when checking API specifics.

Do not commit `.env.local` or other files containing LiveKit credentials.
