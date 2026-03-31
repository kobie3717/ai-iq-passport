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
