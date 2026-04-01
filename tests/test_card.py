"""Tests for AgentCard."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from passport.card import AgentCard, TaskSummary
from passport.skills import Skill
from passport.reputation import Reputation


def test_create_card():
    """Test creating a new agent card."""
    card = AgentCard.create(name="TestAgent")

    assert card.name == "TestAgent"
    assert card.agent_id.startswith("agent-")
    assert len(card.skills) == 0
    assert card.reputation is None
    assert card.signature is None


def test_create_card_with_id():
    """Test creating card with specific ID."""
    card = AgentCard.create(name="TestAgent", agent_id="custom-id-123")

    assert card.agent_id == "custom-id-123"


def test_add_skill():
    """Test adding skills to card."""
    card = AgentCard.create(name="TestAgent")
    skill = Skill(name="python", confidence=0.8, evidence_count=10)

    card.add_skill(skill)

    assert len(card.skills) == 1
    assert card.skills[0].name == "python"
    assert card.skills[0].confidence == 0.8


def test_update_existing_skill():
    """Test updating an existing skill."""
    card = AgentCard.create(name="TestAgent")
    skill1 = Skill(name="python", confidence=0.8)
    skill2 = Skill(name="python", confidence=0.9, evidence_count=20)

    card.add_skill(skill1)
    card.add_skill(skill2)

    assert len(card.skills) == 1
    assert card.skills[0].confidence == 0.9
    assert card.skills[0].evidence_count == 20


def test_remove_skill():
    """Test removing a skill."""
    card = AgentCard.create(name="TestAgent")
    card.add_skill(Skill(name="python", confidence=0.8))
    card.add_skill(Skill(name="javascript", confidence=0.7))

    removed = card.remove_skill("python")

    assert removed is True
    assert len(card.skills) == 1
    assert card.skills[0].name == "javascript"


def test_remove_nonexistent_skill():
    """Test removing a skill that doesn't exist."""
    card = AgentCard.create(name="TestAgent")

    removed = card.remove_skill("python")

    assert removed is False


def test_get_skill():
    """Test getting a skill by name."""
    card = AgentCard.create(name="TestAgent")
    skill = Skill(name="python", confidence=0.8)
    card.add_skill(skill)

    found = card.get_skill("python")

    assert found is not None
    assert found.name == "python"
    assert found.confidence == 0.8


def test_add_trait():
    """Test adding traits."""
    card = AgentCard.create(name="TestAgent")

    card.add_trait("role", "developer")
    card.add_trait("team", "backend")

    assert card.traits["role"] == "developer"
    assert card.traits["team"] == "backend"


def test_to_dict():
    """Test converting card to dictionary."""
    card = AgentCard.create(name="TestAgent", agent_id="test-123")
    card.add_skill(Skill(name="python", confidence=0.8))

    data = card.to_dict()

    assert data["agent_id"] == "test-123"
    assert data["name"] == "TestAgent"
    assert len(data["skills"]) == 1
    assert data["skills"][0]["name"] == "python"


def test_from_dict():
    """Test creating card from dictionary."""
    data = {
        "agent_id": "test-123",
        "name": "TestAgent",
        "version": "0.1.0",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-02T00:00:00",
        "skills": [
            {
                "name": "python",
                "confidence": 0.8,
                "evidence_count": 10,
                "last_used": "2026-01-01T00:00:00",
                "tags": ["programming"],
            }
        ],
        "reputation": None,
        "task_history": {
            "total_tasks": 10,
            "completed_tasks": 8,
            "failed_tasks": 2,
            "success_rate": 0.8,
            "total_feedback_score": 0.0,
            "avg_feedback_score": 0.0,
        },
        "traits": {"role": "developer"},
        "signature": None,
    }

    card = AgentCard.from_dict(data)

    assert card.agent_id == "test-123"
    assert card.name == "TestAgent"
    assert len(card.skills) == 1
    assert card.skills[0].name == "python"
    assert card.traits["role"] == "developer"


def test_json_serialization():
    """Test JSON serialization round-trip."""
    card1 = AgentCard.create(name="TestAgent")
    card1.add_skill(Skill(name="python", confidence=0.8))
    card1.add_trait("role", "developer")

    json_str = card1.to_json()
    card2 = AgentCard.from_json(json_str)

    assert card2.name == card1.name
    assert card2.agent_id == card1.agent_id
    assert len(card2.skills) == len(card1.skills)
    assert card2.traits == card1.traits


def test_save_and_load():
    """Test saving and loading from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_passport.json"

        card1 = AgentCard.create(name="TestAgent")
        card1.add_skill(Skill(name="python", confidence=0.8))

        card1.save(str(filepath))

        card2 = AgentCard.load(str(filepath))

        assert card2.name == card1.name
        assert len(card2.skills) == 1


def test_summary():
    """Test generating summary."""
    card = AgentCard.create(name="TestAgent")
    card.add_skill(Skill(name="python", confidence=0.9, evidence_count=50))
    card.add_skill(Skill(name="javascript", confidence=0.7, evidence_count=20))

    summary = card.summary()

    assert "TestAgent" in summary
    assert "python" in summary
    assert "javascript" in summary
    assert "0.90" in summary  # confidence


def test_task_summary():
    """Test TaskSummary data class."""
    task_summary = TaskSummary(
        total_tasks=10,
        completed_tasks=8,
        failed_tasks=2,
        success_rate=0.8,
    )

    assert task_summary.total_tasks == 10
    assert task_summary.success_rate == 0.8

    data = task_summary.to_dict()
    task_summary2 = TaskSummary.from_dict(data)

    assert task_summary2.total_tasks == 10


# New v0.3.0 tests for predictions and task log

def test_card_predictions_field():
    """Test predictions field in card."""
    card = AgentCard.create(name="TestAgent")

    assert card.predictions == []
    assert isinstance(card.predictions, list)


def test_card_task_log_field():
    """Test task_log field in card."""
    card = AgentCard.create(name="TestAgent")

    assert card.task_log == []
    assert isinstance(card.task_log, list)


def test_log_task():
    """Test logging a task."""
    card = AgentCard.create(name="TestAgent")

    card.log_task("Fix authentication bug", "success", ["bug-fix", "auth"])

    assert len(card.task_log) == 1
    assert card.task_log[0]["task"] == "Fix authentication bug"
    assert card.task_log[0]["outcome"] == "success"
    assert card.task_log[0]["tags"] == ["bug-fix", "auth"]
    assert "timestamp" in card.task_log[0]


def test_log_multiple_tasks():
    """Test logging multiple tasks."""
    card = AgentCard.create(name="TestAgent")

    card.log_task("Task 1", "success", ["feature"])
    card.log_task("Task 2", "failure", ["bug"])
    card.log_task("Task 3", "success", ["refactor"])

    assert len(card.task_log) == 3


def test_task_stats_empty():
    """Test task stats with no tasks."""
    card = AgentCard.create(name="TestAgent")

    stats = card.task_stats()

    assert stats["total"] == 0
    assert stats["success_count"] == 0
    assert stats["failure_count"] == 0
    assert stats["success_rate"] == 0.0
    assert stats["tags_distribution"] == {}


def test_task_stats():
    """Test task stats calculation."""
    card = AgentCard.create(name="TestAgent")

    card.log_task("Task 1", "success", ["feature", "frontend"])
    card.log_task("Task 2", "failure", ["bug"])
    card.log_task("Task 3", "success", ["feature", "backend"])
    card.log_task("Task 4", "success", ["refactor"])

    stats = card.task_stats()

    assert stats["total"] == 4
    assert stats["success_count"] == 3
    assert stats["failure_count"] == 1
    assert stats["success_rate"] == 0.75
    assert stats["tags_distribution"]["feature"] == 2
    assert stats["tags_distribution"]["bug"] == 1


def test_card_serialization_with_predictions():
    """Test card serialization includes predictions."""
    card = AgentCard.create(name="TestAgent")
    card.predictions = [
        {
            "statement": "AI will improve",
            "confidence": 0.8,
            "created_at": "2026-01-01T00:00:00",
            "deadline": "2026-12-31",
            "outcome": "open",
            "resolved_at": None
        }
    ]

    data = card.to_dict()

    assert "predictions" in data
    assert len(data["predictions"]) == 1
    assert data["predictions"][0]["statement"] == "AI will improve"


def test_card_serialization_with_task_log():
    """Test card serialization includes task log."""
    card = AgentCard.create(name="TestAgent")
    card.log_task("Test task", "success", ["test"])

    data = card.to_dict()

    assert "task_log" in data
    assert len(data["task_log"]) == 1
    assert data["task_log"][0]["task"] == "Test task"


def test_card_deserialization_with_predictions_and_task_log():
    """Test card deserialization with predictions and task log."""
    data = {
        "agent_id": "test-123",
        "name": "TestAgent",
        "version": "0.3.0",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-02T00:00:00",
        "skills": [],
        "reputation": None,
        "task_history": {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0,
            "total_feedback_score": 0.0,
            "avg_feedback_score": 0.0,
        },
        "traits": {},
        "signature": None,
        "predictions": [
            {
                "statement": "Test prediction",
                "confidence": 0.9,
                "created_at": "2026-01-01T00:00:00",
                "deadline": "2026-12-31",
                "outcome": "confirmed",
                "resolved_at": "2026-06-01T00:00:00"
            }
        ],
        "task_log": [
            {
                "task": "Test task",
                "timestamp": "2026-01-01T00:00:00",
                "outcome": "success",
                "tags": ["test"]
            }
        ]
    }

    card = AgentCard.from_dict(data)

    assert len(card.predictions) == 1
    assert card.predictions[0]["statement"] == "Test prediction"
    assert len(card.task_log) == 1
    assert card.task_log[0]["task"] == "Test task"


def test_card_backwards_compatible():
    """Test cards without predictions/task_log still work."""
    data = {
        "agent_id": "test-123",
        "name": "TestAgent",
        "version": "0.1.0",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-02T00:00:00",
        "skills": [],
        "reputation": None,
        "task_history": {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0,
            "total_feedback_score": 0.0,
            "avg_feedback_score": 0.0,
        },
        "traits": {},
        "signature": None,
    }

    card = AgentCard.from_dict(data)

    assert card.predictions == []
    assert card.task_log == []


# New v0.4.0 tests for passport age tracking

def test_card_has_last_refreshed():
    """Test card has last_refreshed field."""
    card = AgentCard.create(name="TestAgent")

    assert hasattr(card, 'last_refreshed')
    assert isinstance(card.last_refreshed, datetime)


def test_card_age_days():
    """Test passport age calculation."""
    card = AgentCard.create(name="TestAgent")

    age = card.age_days()

    assert age >= 0


def test_card_age_check_no_stale_skills():
    """Test age_check with fresh skills."""
    from datetime import timedelta
    from passport.skills import Skill

    card = AgentCard.create(name="TestAgent")
    card.add_skill(Skill(name="python", confidence=0.8))

    stale_skills, metadata = card.age_check()

    assert len(stale_skills) == 0
    assert metadata["passport_age_days"] >= 0
    assert metadata["stale_skills_count"] == 0
    assert metadata["total_skills"] == 1
    assert metadata["freshness_score"] == 1.0


def test_card_age_check_with_stale_skills():
    """Test age_check with stale skills."""
    from datetime import timedelta
    from passport.skills import Skill

    card = AgentCard.create(name="TestAgent")

    # Add fresh skill
    fresh_skill = Skill(name="python", confidence=0.8)
    card.add_skill(fresh_skill)

    # Add stale skill
    stale_skill = Skill(name="javascript", confidence=0.7)
    stale_skill.last_used = datetime.now() - timedelta(days=100)
    card.add_skill(stale_skill)

    stale_skills, metadata = card.age_check(stale_threshold_days=30)

    assert len(stale_skills) == 1
    assert stale_skills[0].name == "javascript"
    assert metadata["stale_skills_count"] == 1
    assert metadata["total_skills"] == 2
    assert 0.0 <= metadata["freshness_score"] < 1.0


def test_card_refresh():
    """Test refresh updates last_refreshed."""
    card = AgentCard.create(name="TestAgent")

    original_refresh = card.last_refreshed

    # Wait a tiny bit
    import time
    time.sleep(0.01)

    card.refresh()

    assert card.last_refreshed > original_refresh


def test_card_to_dict_includes_age_metadata():
    """Test to_dict includes age metadata."""
    card = AgentCard.create(name="TestAgent")

    data = card.to_dict()

    assert "last_refreshed" in data
    assert "passport_age_days" in data
    assert "stale_skills_count" in data
    assert "freshness_score" in data


def test_card_from_dict_backwards_compatible_refresh():
    """Test cards without last_refreshed still work."""
    data = {
        "agent_id": "test-123",
        "name": "TestAgent",
        "version": "0.1.0",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-02T00:00:00",
        "skills": [],
        "reputation": None,
        "task_history": {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0,
            "total_feedback_score": 0.0,
            "avg_feedback_score": 0.0,
        },
        "traits": {},
        "signature": None,
    }

    card = AgentCard.from_dict(data)

    # Should default to updated_at
    assert card.last_refreshed == card.updated_at
