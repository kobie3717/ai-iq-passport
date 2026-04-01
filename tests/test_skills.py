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


# New v0.3.0 tests for FSRS and skill decay

def test_skill_fsrs_fields():
    """Test FSRS fields in skill."""
    skill = Skill(
        name="python",
        confidence=0.8,
        fsrs_stability=5.0,
        fsrs_difficulty=6.0,
        last_reviewed=datetime.now() - timedelta(days=10),
        stale=False
    )

    assert skill.fsrs_stability == 5.0
    assert skill.fsrs_difficulty == 6.0
    assert skill.last_reviewed is not None
    assert skill.stale is False


def test_skill_age_days():
    """Test age_days calculation."""
    skill = Skill(name="python")
    skill.last_used = datetime.now() - timedelta(days=50)

    age = skill.age_days()

    assert age == 50


def test_skill_age_days_with_review():
    """Test age_days uses last_reviewed if available."""
    skill = Skill(name="python")
    skill.last_used = datetime.now() - timedelta(days=100)
    skill.last_reviewed = datetime.now() - timedelta(days=20)

    age = skill.age_days()

    assert age == 20


def test_skill_is_stale():
    """Test is_stale detection."""
    old_skill = Skill(name="python")
    old_skill.last_used = datetime.now() - timedelta(days=100)

    recent_skill = Skill(name="javascript")
    recent_skill.last_used = datetime.now() - timedelta(days=30)

    assert old_skill.is_stale(threshold_days=90) is True
    assert recent_skill.is_stale(threshold_days=90) is False


def test_skill_decayed_confidence_fresh():
    """Test decayed_confidence for fresh skills (< 30 days)."""
    skill = Skill(name="python", confidence=0.8)
    skill.last_used = datetime.now() - timedelta(days=20)

    decayed = skill.decayed_confidence()

    assert decayed == 0.8  # No decay within 30 days


def test_skill_decayed_confidence_stale():
    """Test decayed_confidence for stale skills."""
    skill = Skill(name="python", confidence=0.8)
    skill.last_used = datetime.now() - timedelta(days=100)

    decayed = skill.decayed_confidence()

    # 100 days - 30 days = 70 days = 10 weeks
    # 10 weeks * 1% = 10% decay
    expected = 0.8 - 0.10
    assert abs(decayed - expected) < 0.01


def test_skill_decayed_confidence_max_decay():
    """Test decayed_confidence caps at 50% decay."""
    skill = Skill(name="python", confidence=1.0)
    skill.last_used = datetime.now() - timedelta(days=400)

    decayed = skill.decayed_confidence()

    # Should cap at 50% decay
    assert decayed == 0.5


def test_skill_decayed_confidence_min():
    """Test decayed_confidence doesn't go below 0."""
    skill = Skill(name="python", confidence=0.3)
    skill.last_used = datetime.now() - timedelta(days=400)

    decayed = skill.decayed_confidence()

    assert decayed >= 0.0


def test_skill_serialization_with_fsrs():
    """Test skill serialization includes FSRS fields."""
    skill = Skill(
        name="python",
        confidence=0.8,
        fsrs_stability=5.0,
        fsrs_difficulty=6.0,
        last_reviewed=datetime.now(),
        stale=False
    )

    data = skill.to_dict()

    assert "fsrs_stability" in data
    assert "fsrs_difficulty" in data
    assert "last_reviewed" in data
    assert "stale" in data
    assert "decayed_confidence" in data
    assert data["fsrs_stability"] == 5.0
    assert data["fsrs_difficulty"] == 6.0


def test_skill_deserialization_with_fsrs():
    """Test skill deserialization with FSRS fields."""
    now = datetime.now()
    data = {
        "name": "python",
        "confidence": 0.8,
        "evidence_count": 10,
        "last_used": now.isoformat(),
        "tags": ["programming"],
        "fsrs_stability": 5.0,
        "fsrs_difficulty": 6.0,
        "last_reviewed": now.isoformat(),
        "stale": False
    }

    skill = Skill.from_dict(data)

    assert skill.fsrs_stability == 5.0
    assert skill.fsrs_difficulty == 6.0
    assert skill.last_reviewed is not None
    assert skill.stale is False


def test_skill_deserialization_backwards_compatible():
    """Test skills without FSRS fields still work."""
    now = datetime.now()
    data = {
        "name": "python",
        "confidence": 0.8,
        "evidence_count": 10,
        "last_used": now.isoformat(),
        "tags": ["programming"]
    }

    skill = Skill.from_dict(data)

    assert skill.name == "python"
    assert skill.fsrs_stability == 0.0
    assert skill.fsrs_difficulty == 5.0  # Default
    assert skill.last_reviewed is None
    assert skill.stale is False


# Tamper-resistance tests (v0.4.0)

def test_skill_high_confidence_low_stability_suspicious():
    """Test that high confidence + low stability is detectable as suspicious.

    A skill with high confidence (0.9) but low stability (0.5) hasn't been
    tested over time and should raise suspicion during review.
    """
    suspicious_skill = Skill(
        name="expert-skill",
        confidence=0.9,
        evidence_count=100,
        fsrs_stability=0.5,  # Low stability despite high confidence
        fsrs_difficulty=8.0
    )

    # Reviewers can spot this: high confidence but not stable
    assert suspicious_skill.confidence > 0.8
    assert suspicious_skill.fsrs_stability < 1.0

    # Red flag: stability should grow with repeated success
    # A genuine high-confidence skill should have stability > 5.0
    is_suspicious = suspicious_skill.confidence > 0.8 and suspicious_skill.fsrs_stability < 2.0
    assert is_suspicious is True


def test_skill_fsrs_difficulty_validation():
    """Test that FSRS difficulty provides context for confidence.

    High difficulty + high confidence = genuinely impressive
    Low difficulty + high confidence = might be gaming
    """
    # Easy skill with high confidence - could be gaming
    easy_skill = Skill(
        name="hello-world",
        confidence=0.95,
        fsrs_stability=10.0,
        fsrs_difficulty=2.0  # Very easy
    )

    # Hard skill with high confidence - genuinely impressive
    hard_skill = Skill(
        name="distributed-systems",
        confidence=0.95,
        fsrs_stability=10.0,
        fsrs_difficulty=9.0  # Very difficult
    )

    assert easy_skill.confidence == hard_skill.confidence
    assert hard_skill.fsrs_difficulty > easy_skill.fsrs_difficulty

    # Reviewers can weigh difficulty when assessing claims
