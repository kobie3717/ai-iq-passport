"""Tests for MCP server functionality."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from passport.mcp_server import (
    mcp,
    passport_generate,
    passport_verify,
    passport_skills,
    passport_reputation,
    get_current_passport,
    get_passport_by_id,
    DEFAULT_PASSPORT_DIR,
)
from passport.card import AgentCard, Skill
from passport.signer import generate_keypair, Signer


@pytest.fixture
def temp_passport_dir(monkeypatch):
    """Create a temporary passport directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        passport_dir = tmpdir_path / "passport"
        registry_dir = passport_dir / "registry"

        # Patch module-level constants
        monkeypatch.setattr("passport.mcp_server.DEFAULT_PASSPORT_DIR", passport_dir)
        monkeypatch.setattr("passport.mcp_server.DEFAULT_PASSPORT_PATH", passport_dir / "passport.json")
        monkeypatch.setattr("passport.mcp_server.DEFAULT_REGISTRY_DIR", registry_dir)

        yield passport_dir


def test_mcp_server_initialization():
    """Test that the MCP server initializes correctly."""
    assert mcp.name == "ai-iq-passport"
    assert "passport" in str(mcp.instructions).lower()


def test_passport_generate_basic(temp_passport_dir):
    """Test basic passport generation."""
    result = passport_generate(name="TestAgent")

    assert result["success"] is True
    assert result["name"] == "TestAgent"
    assert "agent_id" in result
    assert result["skills_imported"] == 0
    assert result["reputation_score"] is None

    # Verify passport was created
    passport_path = Path(result["passport_path"])
    assert passport_path.exists()

    # Load and verify
    card = AgentCard.load(str(passport_path))
    assert card.name == "TestAgent"
    assert card.agent_id == result["agent_id"]


def test_passport_generate_with_custom_id(temp_passport_dir):
    """Test passport generation with custom agent ID."""
    result = passport_generate(name="CustomAgent", agent_id="agent-custom-123")

    assert result["success"] is True
    assert result["agent_id"] == "agent-custom-123"


def test_passport_generate_nonexistent_ai_iq_db(temp_passport_dir):
    """Test passport generation with non-existent AI-IQ database."""
    result = passport_generate(
        name="TestAgent",
        ai_iq_db="/nonexistent/path/memories.db"
    )

    assert result["success"] is False
    assert "not found" in result["error"]


def test_passport_verify_unsigned(temp_passport_dir):
    """Test verifying an unsigned passport."""
    # Create unsigned passport
    card = AgentCard.create(name="TestAgent")
    passport_json = card.to_json()

    result = passport_verify(passport_json)

    assert result["verified"] is False
    assert "no signature" in result["error"].lower()


def test_passport_verify_signed(temp_passport_dir):
    """Test verifying a signed passport."""
    # Generate keys
    keys_dir = temp_passport_dir / "keys"
    private_key_path, public_key_path = generate_keypair(str(keys_dir))

    # Create and sign passport
    card = AgentCard.create(name="TestAgent")
    signer = Signer.from_file(private_key_path)
    signature = signer.sign_card(card.to_dict())
    card.signature = signature

    passport_json = card.to_json()

    result = passport_verify(passport_json, public_key_path=public_key_path)

    assert result["verified"] is True
    assert result["agent_id"] == card.agent_id
    assert "signature" in result


def test_passport_verify_invalid_json():
    """Test verifying invalid JSON."""
    result = passport_verify("not valid json")

    assert result["verified"] is False
    assert "Invalid JSON" in result["error"]


def test_passport_skills_current(temp_passport_dir):
    """Test getting skills for current agent."""
    # Create passport with skills
    card = AgentCard.create(name="SkillfulAgent")
    card.add_skill(Skill(name="Python", confidence=0.9, evidence_count=50))
    card.add_skill(Skill(name="JavaScript", confidence=0.7, evidence_count=30))
    card.add_skill(Skill(name="Rust", confidence=0.6, evidence_count=10))

    temp_passport_dir.mkdir(parents=True, exist_ok=True)
    passport_path = temp_passport_dir / "passport.json"
    card.save(str(passport_path))

    result = passport_skills(agent_id="current", top_n=2)

    assert result["success"] is True
    assert result["agent_name"] == "SkillfulAgent"
    assert result["total_skills"] == 3
    assert len(result["top_skills"]) == 2

    # Should be sorted by confidence
    assert result["top_skills"][0]["name"] == "Python"
    assert result["top_skills"][0]["confidence"] == 0.9
    assert result["top_skills"][1]["name"] == "JavaScript"


def test_passport_skills_nonexistent_agent(temp_passport_dir):
    """Test getting skills for non-existent agent."""
    result = passport_skills(agent_id="agent-nonexistent")

    assert result["success"] is False
    assert "found" in result["error"].lower()


def test_passport_reputation_current(temp_passport_dir):
    """Test getting reputation for current agent."""
    from passport.reputation import Reputation

    # Create passport with reputation
    card = AgentCard.create(name="ReputableAgent")
    card.reputation = Reputation(
        overall_score=0.85,
        feedback_score=0.9,
        prediction_accuracy=0.8,
        task_completion_rate=0.9,
        consistency_score=0.7,
        total_feedback=100,
        total_predictions=50,
        total_tasks=75,
    )

    temp_passport_dir.mkdir(parents=True, exist_ok=True)
    passport_path = temp_passport_dir / "passport.json"
    card.save(str(passport_path))

    result = passport_reputation(agent_id="current")

    assert result["success"] is True
    assert result["has_reputation"] is True
    assert result["overall_score"] == 0.85
    assert result["breakdown"]["feedback_score"] == 0.9
    assert result["breakdown"]["prediction_accuracy"] == 0.8
    assert result["counts"]["total_feedback"] == 100


def test_passport_reputation_no_reputation(temp_passport_dir):
    """Test getting reputation for agent without reputation data."""
    # Create passport without reputation
    card = AgentCard.create(name="NewAgent")
    temp_passport_dir.mkdir(parents=True, exist_ok=True)
    passport_path = temp_passport_dir / "passport.json"
    card.save(str(passport_path))

    result = passport_reputation(agent_id="current")

    assert result["success"] is True
    assert result["has_reputation"] is False
    assert "No reputation data" in result["message"]


def test_get_current_passport_resource(temp_passport_dir):
    """Test getting current passport as MCP resource."""
    # Create passport
    card = AgentCard.create(name="ResourceAgent")
    temp_passport_dir.mkdir(parents=True, exist_ok=True)
    passport_path = temp_passport_dir / "passport.json"
    card.save(str(passport_path))

    # Get resource
    resource_json = get_current_passport()
    resource_data = json.loads(resource_json)

    assert resource_data["name"] == "ResourceAgent"
    assert resource_data["agent_id"] == card.agent_id


def test_get_current_passport_not_found(temp_passport_dir):
    """Test getting current passport when none exists."""
    resource_json = get_current_passport()
    resource_data = json.loads(resource_json)

    assert "error" in resource_data
    assert "No passport found" in resource_data["error"]


def test_get_passport_by_id_resource(temp_passport_dir):
    """Test getting passport by ID as MCP resource."""
    # Create passport
    card = AgentCard.create(name="IDAgent", agent_id="agent-test-123")
    registry_path = temp_passport_dir / "registry" / "agent-test-123.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    card.save(str(registry_path))

    # Get resource
    resource_json = get_passport_by_id("agent-test-123")
    resource_data = json.loads(resource_json)

    assert resource_data["name"] == "IDAgent"
    assert resource_data["agent_id"] == "agent-test-123"


def test_get_passport_by_id_not_found(temp_passport_dir):
    """Test getting non-existent passport by ID."""
    resource_json = get_passport_by_id("agent-nonexistent")
    resource_data = json.loads(resource_json)

    assert "error" in resource_data
    assert "not found" in resource_data["error"]
