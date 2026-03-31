"""Tests for adapter modules (A2A, MCP, JSON)."""

import json
import tempfile
from pathlib import Path

import pytest

from passport.card import AgentCard
from passport.skills import Skill
from passport.reputation import Reputation
from passport.adapters import export_a2a, export_mcp, export_json, import_json


@pytest.fixture
def sample_card():
    """Create a sample agent card for testing."""
    card = AgentCard.create(name="TestAgent", agent_id="agent-123")

    # Add skills
    card.add_skill(Skill(
        name="Python development",
        confidence=0.9,
        evidence_count=45,
        tags=["programming", "backend"]
    ))
    card.add_skill(Skill(
        name="API design",
        confidence=0.85,
        evidence_count=30,
        tags=["architecture", "rest"]
    ))

    # Add reputation
    card.reputation = Reputation(
        overall_score=0.82,
        feedback_score=0.85,
        prediction_accuracy=0.80,
        task_completion_rate=0.95,
        consistency_score=0.70,
        total_tasks=50,
        total_feedback=100
    )

    # Add task history
    card.task_history.total_tasks = 50
    card.task_history.completed_tasks = 48
    card.task_history.failed_tasks = 2
    card.task_history.success_rate = 0.96
    card.task_history.avg_feedback_score = 0.85

    # Add traits
    card.add_trait("framework", "CrewAI")
    card.add_trait("model", "claude-sonnet-4.5")

    return card


class TestA2AAdapter:
    """Tests for A2A adapter."""

    def test_export_a2a_structure(self, sample_card):
        """Test A2A export produces valid structure."""
        card_dict = sample_card.to_dict()
        a2a_card = export_a2a(card_dict)

        # Check required fields
        assert a2a_card["@context"] == "https://a2aproject.org/schema"
        assert a2a_card["@type"] == "AgentCard"
        assert a2a_card["id"] == "agent-123"
        assert a2a_card["name"] == "TestAgent"
        assert "description" in a2a_card
        assert "version" in a2a_card
        assert "created" in a2a_card
        assert "updated" in a2a_card

    def test_export_a2a_capabilities(self, sample_card):
        """Test A2A capabilities mapping."""
        card_dict = sample_card.to_dict()
        a2a_card = export_a2a(card_dict)

        capabilities = a2a_card["capabilities"]
        assert len(capabilities) == 2

        # Check first capability
        cap1 = capabilities[0]
        assert cap1["name"] == "Python development"
        assert cap1["confidence"] == 0.9
        assert cap1["evidence_count"] == 45
        assert "programming" in cap1["tags"]
        assert "backend" in cap1["tags"]

    def test_export_a2a_reputation(self, sample_card):
        """Test A2A reputation mapping."""
        card_dict = sample_card.to_dict()
        a2a_card = export_a2a(card_dict)

        reputation = a2a_card["reputation"]
        assert reputation["score"] == 0.82
        assert reputation["feedback_score"] == 0.85
        assert reputation["prediction_accuracy"] == 0.80
        assert reputation["task_completion_rate"] == 0.95
        assert reputation["total_tasks"] == 50

    def test_export_a2a_task_history(self, sample_card):
        """Test A2A task history mapping."""
        card_dict = sample_card.to_dict()
        a2a_card = export_a2a(card_dict)

        task_history = a2a_card["task_history"]
        assert task_history["total"] == 50
        assert task_history["completed"] == 48
        assert task_history["success_rate"] == 0.96

    def test_export_a2a_metadata(self, sample_card):
        """Test A2A metadata (traits) mapping."""
        card_dict = sample_card.to_dict()
        a2a_card = export_a2a(card_dict)

        metadata = a2a_card["metadata"]
        assert metadata["framework"] == "CrewAI"
        assert metadata["model"] == "claude-sonnet-4.5"

    def test_export_a2a_without_optional_fields(self):
        """Test A2A export with minimal card."""
        card = AgentCard.create(name="MinimalAgent", agent_id="agent-minimal")
        card_dict = card.to_dict()
        a2a_card = export_a2a(card_dict)

        # Should have required fields
        assert a2a_card["id"] == "agent-minimal"
        assert a2a_card["name"] == "MinimalAgent"
        assert a2a_card["capabilities"] == []

        # Should not have optional fields
        assert "reputation" not in a2a_card
        assert "task_history" not in a2a_card
        assert "metadata" not in a2a_card

    def test_export_a2a_with_signature(self, sample_card):
        """Test A2A export preserves signature."""
        sample_card.signature = "base64encodedSignature=="
        card_dict = sample_card.to_dict()
        a2a_card = export_a2a(card_dict)

        assert a2a_card["signature"] == "base64encodedSignature=="


class TestMCPAdapter:
    """Tests for MCP adapter."""

    def test_export_mcp_structure(self, sample_card):
        """Test MCP export produces valid resource structure."""
        card_dict = sample_card.to_dict()
        mcp_resource = export_mcp(card_dict)

        # Check required fields
        assert mcp_resource["uri"] == "passport://agent-123"
        assert mcp_resource["name"] == "Agent Passport: TestAgent"
        assert "description" in mcp_resource
        assert mcp_resource["mimeType"] == "application/json"
        assert "contents" in mcp_resource
        assert "annotations" in mcp_resource

    def test_export_mcp_description(self, sample_card):
        """Test MCP description includes key information."""
        card_dict = sample_card.to_dict()
        mcp_resource = export_mcp(card_dict)

        description = mcp_resource["description"]
        assert "TestAgent" in description
        assert "Python development" in description
        assert "API design" in description
        assert "0.82" in description  # Reputation score
        assert "50" in description  # Task count

    def test_export_mcp_description_truncates_skills(self):
        """Test MCP description truncates long skill lists."""
        card = AgentCard.create(name="SkillfulAgent", agent_id="agent-skills")

        # Add 8 skills
        for i in range(8):
            card.add_skill(Skill(name=f"Skill {i+1}", confidence=0.8))

        card_dict = card.to_dict()
        mcp_resource = export_mcp(card_dict)

        description = mcp_resource["description"]
        # Should show first 5 and "and 3 more"
        assert "Skill 1" in description
        assert "Skill 5" in description
        assert "and 3 more" in description

    def test_export_mcp_annotations(self, sample_card):
        """Test MCP annotations contain metadata."""
        card_dict = sample_card.to_dict()
        mcp_resource = export_mcp(card_dict)

        annotations = mcp_resource["annotations"]
        assert annotations["agent_id"] == "agent-123"
        assert annotations["agent_name"] == "TestAgent"
        assert annotations["skill_count"] == 2
        assert annotations["verified"] is False  # No signature
        assert annotations["reputation_score"] == 0.82

    def test_export_mcp_verified_annotation(self, sample_card):
        """Test MCP verified annotation when signed."""
        sample_card.signature = "base64encodedSignature=="
        card_dict = sample_card.to_dict()
        mcp_resource = export_mcp(card_dict)

        assert mcp_resource["annotations"]["verified"] is True

    def test_export_mcp_contents(self, sample_card):
        """Test MCP contents field contains full card."""
        card_dict = sample_card.to_dict()
        mcp_resource = export_mcp(card_dict)

        contents = mcp_resource["contents"]
        assert contents["agent_id"] == "agent-123"
        assert contents["name"] == "TestAgent"
        assert len(contents["skills"]) == 2

    def test_export_mcp_without_optional_fields(self):
        """Test MCP export with minimal card."""
        card = AgentCard.create(name="MinimalAgent", agent_id="agent-minimal")
        card_dict = card.to_dict()
        mcp_resource = export_mcp(card_dict)

        # Should have required fields
        assert mcp_resource["uri"] == "passport://agent-minimal"
        assert mcp_resource["name"] == "Agent Passport: MinimalAgent"

        annotations = mcp_resource["annotations"]
        assert annotations["skill_count"] == 0
        assert annotations["verified"] is False
        assert "reputation_score" not in annotations


class TestJSONAdapter:
    """Tests for JSON import/export."""

    def test_export_json(self, sample_card):
        """Test JSON export writes file correctly."""
        card_dict = sample_card.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_card.json"
            export_json(card_dict, str(output_path))

            # Verify file exists
            assert output_path.exists()

            # Read and verify contents
            with open(output_path, "r") as f:
                loaded = json.load(f)

            assert loaded["agent_id"] == "agent-123"
            assert loaded["name"] == "TestAgent"
            assert len(loaded["skills"]) == 2

    def test_import_json(self, sample_card):
        """Test JSON import reads file correctly."""
        card_dict = sample_card.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_card.json"

            # Write file
            with open(file_path, "w") as f:
                json.dump(card_dict, f)

            # Import and verify
            loaded = import_json(str(file_path))

            assert loaded["agent_id"] == "agent-123"
            assert loaded["name"] == "TestAgent"
            assert len(loaded["skills"]) == 2
            assert loaded["skills"][0]["name"] == "Python development"

    def test_export_json_custom_indent(self, sample_card):
        """Test JSON export with custom indentation."""
        card_dict = sample_card.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_card.json"
            export_json(card_dict, str(output_path), indent=4)

            # Read raw content
            with open(output_path, "r") as f:
                content = f.read()

            # Verify indentation (4 spaces)
            assert "    \"agent_id\"" in content

    def test_roundtrip_json(self, sample_card):
        """Test JSON export and import roundtrip."""
        original_dict = sample_card.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "roundtrip.json"

            # Export
            export_json(original_dict, str(file_path))

            # Import
            loaded_dict = import_json(str(file_path))

            # Verify match
            assert loaded_dict["agent_id"] == original_dict["agent_id"]
            assert loaded_dict["name"] == original_dict["name"]
            assert len(loaded_dict["skills"]) == len(original_dict["skills"])
            assert loaded_dict["reputation"]["overall_score"] == original_dict["reputation"]["overall_score"]
