import os
import random
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

CATALOG_PATH = Path(__file__).with_name("challenges") / "local.json"
CODING_SPEC_PATH = Path(__file__).with_name("challenges") / "coding_specs.json"


class InterviewChallenge(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    challenge_type: str = Field(alias="type")
    difficulty: str
    categories: tuple[str, ...]
    tags: tuple[str, ...]
    prompt: str
    examples: tuple[str, ...]
    constraints: tuple[str, ...]
    interviewer_notes: tuple[str, ...]
    hints: tuple[str, ...]
    source: str = "original"


class ChallengeCatalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    description: str
    challenges: tuple[InterviewChallenge, ...]


class CodingTestCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = Field(default_factory=dict)
    expected: Any


class CodingSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    challenge_id: str
    language: str = "python"
    function_name: str
    starter_code: str
    test_cases: tuple[CodingTestCase, ...]
    timeout_seconds: float = 2.0


class CodingSpecCatalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: int
    description: str
    specs: tuple[CodingSpec, ...]


def challenge_from_mapping(data: dict[str, Any]) -> InterviewChallenge:
    return InterviewChallenge.model_validate(data)


def load_challenges(path: Path = CATALOG_PATH) -> tuple[InterviewChallenge, ...]:
    catalog = ChallengeCatalog.model_validate_json(path.read_text(encoding="utf-8"))
    return catalog.challenges


def load_coding_specs(path: Path = CODING_SPEC_PATH) -> tuple[CodingSpec, ...]:
    catalog = CodingSpecCatalog.model_validate_json(path.read_text(encoding="utf-8"))
    return catalog.specs


def get_coding_spec(
    challenge_id: str,
    specs: tuple[CodingSpec, ...] | None = None,
) -> CodingSpec | None:
    coding_specs = specs or load_coding_specs()
    for spec in coding_specs:
        if spec.challenge_id == challenge_id:
            return spec
    return None


def get_challenge(
    challenge_id: str,
    catalog: tuple[InterviewChallenge, ...] | None = None,
) -> InterviewChallenge:
    challenges = catalog or load_challenges()
    for challenge in challenges:
        if challenge.id == challenge_id:
            return challenge
    raise ValueError(f"Unknown challenge id: {challenge_id}")


def filter_challenges(
    *,
    challenge_type: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    tags: tuple[str, ...] = (),
    catalog: tuple[InterviewChallenge, ...] | None = None,
) -> tuple[InterviewChallenge, ...]:
    challenges = catalog or load_challenges()

    def matches(challenge: InterviewChallenge) -> bool:
        if challenge_type and challenge.challenge_type != challenge_type:
            return False
        if difficulty and challenge.difficulty != difficulty:
            return False
        if category and category not in challenge.categories:
            return False
        return all(tag in challenge.tags for tag in tags)

    return tuple(challenge for challenge in challenges if matches(challenge))


def select_challenge(
    *,
    challenge_id: str | None = None,
    challenge_type: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
    tags: tuple[str, ...] = (),
    seed: str | None = None,
    catalog: tuple[InterviewChallenge, ...] | None = None,
) -> InterviewChallenge:
    challenges = catalog or load_challenges()
    if challenge_id:
        return get_challenge(challenge_id, challenges)

    candidates = filter_challenges(
        challenge_type=challenge_type,
        difficulty=difficulty,
        category=category,
        tags=tags,
        catalog=challenges,
    )
    if not candidates:
        raise ValueError("No challenges match the requested filters")

    chooser = random.Random(seed) if seed is not None else random.SystemRandom()
    return chooser.choice(candidates)


def _env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _env_tags() -> tuple[str, ...]:
    raw_tags = _env_value("INTERVIEWROOM_CHALLENGE_TAGS")
    if not raw_tags:
        return ()
    return tuple(tag.strip() for tag in raw_tags.split(",") if tag.strip())


def select_challenge_from_env() -> InterviewChallenge:
    return select_challenge(
        challenge_id=_env_value("INTERVIEWROOM_CHALLENGE_ID"),
        challenge_type=_env_value("INTERVIEWROOM_CHALLENGE_TYPE"),
        difficulty=_env_value("INTERVIEWROOM_CHALLENGE_DIFFICULTY"),
        category=_env_value("INTERVIEWROOM_CHALLENGE_CATEGORY"),
        tags=_env_tags(),
        seed=_env_value("INTERVIEWROOM_CHALLENGE_SEED"),
    )


DEFAULT_CHALLENGE = get_challenge("minimum-meeting-rooms")
