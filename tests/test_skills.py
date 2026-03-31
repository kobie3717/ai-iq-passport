"""Tests for Skill and SkillManager."""

from datetime import datetime, timedelta
import pytest

from passport.skills import Skill, SkillManager


def test_create_skill():
    """Test creating a skill."""
    skill = Skill(name="python", confidence=0.8, evidence_count=10)

    assert skill.name == "python"
    assert skill.confidence == 0.8
    assert skill.evidence_count == 10


def test_skill_confidence_bounds():
    """Test confidence is clamped to 0.0-1.0."""
    skill1 = Skill(name="test", confidence=1.5)
    assert skill1.confidence == 1.0

    skill2 = Skill(name="test", confidence=-0.5)
    assert skill2.confidence == 0.0


def test_skill_boost():
    """Test boosting skill confidence."""
    skill = Skill(name="python", confidence=0.5)

    skill.boost(0.2)

    assert skill.confidence == 0.7
    assert skill.evidence_count == 1


def test_skill_boost_max():
    """Test boosting doesn't exceed 1.0."""
    skill = Skill(name="python", confidence=0.95)

    skill.boost(0.2)

    assert skill.confidence == 1.0


def test_skill_decay():
    """Test decaying skill confidence."""
    skill = Skill(name="python", confidence=0.8)

    skill.decay(0.2)

    assert abs(skill.confidence - 0.6) < 1e-9


def test_skill_decay_min():
    """Test decay doesn't go below 0.0."""
    skill = Skill(name="python", confidence=0.05)

    skill.decay(0.2)

    assert skill.confidence == 0.0


def test_skill_serialization():
    """Test skill to_dict and from_dict."""
    skill1 = Skill(name="python", confidence=0.8, evidence_count=10, tags=["programming"])

    data = skill1.to_dict()
    skill2 = Skill.from_dict(data)

    assert skill2.name == skill1.name
    assert skill2.confidence == skill1.confidence
    assert skill2.evidence_count == skill1.evidence_count
    assert skill2.tags == skill1.tags


def test_skill_manager_add():
    """Test adding skills to manager."""
    manager = SkillManager()
    skill = Skill(name="python", confidence=0.8)

    manager.add_or_update(skill)

    assert len(manager.skills) == 1
    assert manager.get("python") is not None


def test_skill_manager_update():
    """Test updating existing skill."""
    manager = SkillManager()
    skill1 = Skill(name="python", confidence=0.8)
    skill2 = Skill(name="python", confidence=0.9)

    manager.add_or_update(skill1)
    manager.add_or_update(skill2)

    assert len(manager.skills) == 1
    assert manager.get("python").confidence == 0.9


def test_skill_manager_remove():
    """Test removing skill."""
    manager = SkillManager()
    manager.add_or_update(Skill(name="python"))

    removed = manager.remove("python")

    assert removed is True
    assert len(manager.skills) == 0


def test_skill_manager_boost():
    """Test boosting skill through manager."""
    manager = SkillManager()

    manager.boost_skill("python", 0.1)

    skill = manager.get("python")
    assert skill is not None
    assert skill.confidence > 0.5


def test_skill_manager_record_usage():
    """Test recording skill usage."""
    manager = SkillManager()

    manager.record_usage("python", success=True)

    skill = manager.get("python")
    assert skill is not None
    assert skill.confidence > 0.5


def test_skill_manager_record_failure():
    """Test recording skill failure."""
    manager = SkillManager()
    manager.add_or_update(Skill(name="python", confidence=0.8))

    manager.record_usage("python", success=False)

    skill = manager.get("python")
    assert skill.confidence < 0.8


def test_skill_manager_decay_unused():
    """Test decaying unused skills."""
    manager = SkillManager()

    # Add old skill
    old_skill = Skill(name="python", confidence=0.8)
    old_skill.last_used = datetime.now() - timedelta(days=100)
    manager.add_or_update(old_skill)

    # Add recent skill
    recent_skill = Skill(name="javascript", confidence=0.8)
    manager.add_or_update(recent_skill)

    decayed = manager.decay_unused(days_threshold=90, decay_amount=0.1)

    assert decayed == 1
    assert manager.get("python").confidence < 0.8
    assert manager.get("javascript").confidence == 0.8


def test_skill_manager_top_skills():
    """Test getting top skills."""
    manager = SkillManager()
    manager.add_or_update(Skill(name="python", confidence=0.9))
    manager.add_or_update(Skill(name="javascript", confidence=0.7))
    manager.add_or_update(Skill(name="rust", confidence=0.8))

    top = manager.get_top_skills(2)

    assert len(top) == 2
    assert top[0].name == "python"
    assert top[1].name == "rust"


def test_skill_manager_by_tag():
    """Test getting skills by tag."""
    manager = SkillManager()
    manager.add_or_update(Skill(name="python", tags=["programming", "backend"]))
    manager.add_or_update(Skill(name="react", tags=["programming", "frontend"]))
    manager.add_or_update(Skill(name="communication", tags=["soft-skill"]))

    programming_skills = manager.get_skills_by_tag("programming")

    assert len(programming_skills) == 2
    assert any(s.name == "python" for s in programming_skills)


def test_skill_manager_stats():
    """Test getting skill statistics."""
    manager = SkillManager()
    manager.add_or_update(Skill(name="python", confidence=0.9, evidence_count=50))
    manager.add_or_update(Skill(name="javascript", confidence=0.7, evidence_count=20))

    stats = manager.stats()

    assert stats["total"] == 2
    assert stats["avg_confidence"] == 0.8
    assert stats["total_evidence"] == 70
    assert stats["top_skill"] == "python"


def test_skill_manager_empty_stats():
    """Test stats with no skills."""
    manager = SkillManager()

    stats = manager.stats()

    assert stats["total"] == 0
    assert stats["avg_confidence"] == 0.0
