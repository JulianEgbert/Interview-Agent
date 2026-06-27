import textwrap
from pathlib import Path

from challenges import DEFAULT_CHALLENGE, InterviewChallenge

TEMPLATE_DIR = Path(__file__).with_name("templates")
OPENING_MESSAGE_TEMPLATE_PATH = TEMPLATE_DIR / "opening_message.txt"
INTERVIEWER_INSTRUCTIONS_TEMPLATE_PATH = TEMPLATE_DIR / "interviewer_instructions.md"

RUBRIC_DIMENSIONS = (
    "problem understanding",
    "clarifying questions",
    "communication",
    "algorithmic reasoning",
    "code correctness",
    "edge case handling",
    "testing approach",
    "time and space complexity",
)


def build_opening_message(
    challenge: InterviewChallenge = DEFAULT_CHALLENGE,
    *,
    workspace_path: str | None = None,
) -> str:
    coding_line = f" You can code in {workspace_path}." if workspace_path else ""
    template = OPENING_MESSAGE_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.format(
        challenge_prompt=challenge.prompt,
        coding_line=coding_line,
    )


OPENING_MESSAGE = build_opening_message()


def build_interviewer_instructions(
    challenge: InterviewChallenge = DEFAULT_CHALLENGE,
    *,
    workspace_path: str | None = None,
    function_name: str | None = None,
    has_runnable_tests: bool = False,
) -> str:
    examples = "\n".join(f"- {example}" for example in challenge.examples)
    constraints = "\n".join(f"- {constraint}" for constraint in challenge.constraints)
    notes = "\n".join(f"- {note}" for note in challenge.interviewer_notes)
    hints = "\n".join(
        f"{index}. {hint}" for index, hint in enumerate(challenge.hints, 1)
    )
    rubric = "\n".join(f"- {dimension}" for dimension in RUBRIC_DIMENSIONS)
    categories = ", ".join(challenge.categories)
    tags = ", ".join(challenge.tags)
    coding_workspace = "No local coding workspace is configured for this challenge."
    if workspace_path and function_name:
        coding_workspace = textwrap.dedent(
            f"""\
            The candidate has a local Python workspace at {workspace_path}.
            They should edit solution.py and implement {function_name}.
            You can inspect the current code and run the local tests when the
            candidate asks you to check their solution, says they are ready, or
            reaches a natural debugging checkpoint.
            """
        ).strip()
        if has_runnable_tests:
            coding_workspace += (
                "\nWhen tests fail, do not read out the full answer. Summarize the "
                "failing behavior and ask a targeted debugging question."
            )

    template = INTERVIEWER_INSTRUCTIONS_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.format(
        challenge_title=challenge.title,
        challenge_id=challenge.id,
        challenge_type=challenge.challenge_type,
        difficulty=challenge.difficulty,
        categories=categories,
        tags=tags,
        coding_workspace=coding_workspace,
        challenge_prompt=challenge.prompt,
        examples=examples,
        constraints=constraints,
        interviewer_notes=notes,
        hints=hints,
        rubric_dimensions=rubric,
    )
