"""AI-IQ Passport - Portable AI agent identity & reputation layer."""

from .card import AgentCard, TaskSummary
from .skills import Skill, SkillManager
from .reputation import Reputation, ReputationCalculator
from .predictions import Prediction, PredictionManager
from .task_log import TaskEntry, TaskLog
from .signer import Signer, generate_keypair
from .verifier import Verifier, verify_card

__version__ = "0.4.0"

__all__ = [
    "AgentCard",
    "TaskSummary",
    "Skill",
    "SkillManager",
    "Reputation",
    "ReputationCalculator",
    "Prediction",
    "PredictionManager",
    "TaskEntry",
    "TaskLog",
    "Signer",
    "Verifier",
    "generate_keypair",
    "verify_card",
]
