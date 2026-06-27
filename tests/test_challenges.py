import pytest
from pydantic import ValidationError

from challenges import (
    DEFAULT_CHALLENGE,
    challenge_from_mapping,
    filter_challenges,
    get_challenge,
    load_challenges,
    select_challenge,
)


def test_catalog_loads_multiple_challenge_types() -> None:
    challenges = load_challenges()
    challenge_types = {challenge.challenge_type for challenge in challenges}

    assert len(challenges) >= 8
    assert DEFAULT_CHALLENGE in challenges
    assert {"coding", "backend", "frontend"}.issubset(challenge_types)


def test_get_challenge_preserves_meeting_rooms() -> None:
    challenge = get_challenge("minimum-meeting-rooms")

    assert challenge.title == "Minimum Meeting Rooms"
    assert "intervals" in challenge.tags
    assert "Back-to-back events do not overlap." in challenge.constraints


def test_filter_challenges_by_type_difficulty_and_tag() -> None:
    challenges = filter_challenges(
        challenge_type="coding",
        difficulty="new-grad",
        tags=("stacks",),
    )

    assert [challenge.id for challenge in challenges] == ["undo-redo-editor"]


def test_select_challenge_can_use_id_or_seeded_random() -> None:
    selected_by_id = select_challenge(challenge_id="frontend-filter-state")
    selected_by_seed = select_challenge(
        challenge_type="coding",
        difficulty="new-grad",
        seed="demo",
    )

    assert selected_by_id.challenge_type == "frontend"
    assert selected_by_seed in filter_challenges(
        challenge_type="coding",
        difficulty="new-grad",
    )


def test_select_challenge_fails_for_empty_filter() -> None:
    with pytest.raises(ValueError, match="No challenges match"):
        select_challenge(challenge_type="behavioral")


def test_challenge_model_validates_required_fields() -> None:
    with pytest.raises(ValidationError) as error:
        challenge_from_mapping(
            {
                "id": "missing-prompt",
                "title": "Missing Prompt",
                "type": "coding",
                "difficulty": "new-grad",
                "examples": [],
                "constraints": [],
                "interviewer_notes": [],
                "hints": [],
            }
        )

    assert "prompt" in str(error.value)
