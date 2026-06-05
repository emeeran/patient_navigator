"""Case status state machine — DATA-004."""

from app.core.exceptions import InvalidStateTransitionError

# Allowed transitions from each status (from Case.schema.json x-state-machine)
CASE_TRANSITIONS: dict[str, list[str]] = {
    "new": ["under_review"],
    "under_review": ["hospital_selected", "new"],
    "hospital_selected": ["funding_applied", "under_review"],
    "funding_applied": ["treatment_started", "hospital_selected"],
    "treatment_started": ["closed", "funding_applied"],
    "closed": ["under_review"],
}

CASE_STATUSES = frozenset(CASE_TRANSITIONS.keys())
CASE_PRIORITIES = frozenset(["low", "medium", "high", "critical"])


def validate_transition(current: str, new: str) -> None:
    """Validate that a status transition is allowed.

    Raises InvalidStateTransitionError if the transition is not in the allowed map.
    """
    if current not in CASE_TRANSITIONS:
        raise InvalidStateTransitionError(f"Unknown current status: {current}")

    allowed = CASE_TRANSITIONS[current]
    if new not in allowed:
        raise InvalidStateTransitionError(
            f"Invalid transition: {current} -> {new}. "
            f"Allowed transitions from '{current}': {', '.join(allowed)}"
        )
