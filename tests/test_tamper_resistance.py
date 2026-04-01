"""Integration tests for tamper-resistance features.

These tests validate the 4 anti-gaming features added in v0.4.0:
1. FSRS stability + difficulty import from AI-IQ
2. Prediction detail (not just counts)
3. Skill decay inside passport
4. Task log (append-only audit trail)
"""

from datetime import datetime, timedelta
import pytest

from passport.card import AgentCard
from passport.skills import Skill, SkillManager
from passport.predictions import Prediction, PredictionManager
from passport.task_log import TaskEntry, TaskLog
from passport.reputation import ReputationCalculator


def test_fsrs_stability_difficulty_in_skill():
    """Test that skills include FSRS stability and difficulty."""
    skill = Skill(
        name="python",
        confidence=0.8,
        evidence_count=50,
        fsrs_stability=5.0,
        fsrs_difficulty=6.0
    )

    skill_dict = skill.to_dict()

    assert "fsrs_stability" in skill_dict
    assert "fsrs_difficulty" in skill_dict
    assert skill_dict["fsrs_stability"] == 5.0
    assert skill_dict["fsrs_difficulty"] == 6.0


def test_prediction_detail_auditable():
    """Test that predictions include full detail, not just counts."""
    pred_manager = PredictionManager()

    pred1 = Prediction(
        statement="Python will dominate AI in 2026",
        confidence=0.8,
        created_at="2026-01-01T00:00:00",
        deadline="2026-12-31T23:59:59",
        outcome="confirmed",
        resolved_at="2026-06-15T10:00:00",
        expected_outcome="Python market share > 50%",
        actual_outcome="Python market share = 65%"
    )

    pred_manager.add(pred1)

    # Reviewers can see WHAT was predicted
    pred_list = pred_manager.to_list()
    assert len(pred_list) == 1
    assert pred_list[0]["statement"] == "Python will dominate AI in 2026"
    assert pred_list[0]["expected_outcome"] is not None
    assert pred_list[0]["actual_outcome"] is not None

    # Not just pass/fail counts
    stats = pred_manager.get_stats()
    assert stats["confirmed"] == 1


def test_passport_age_check_detects_stale_skills():
    """Test that passport age_check identifies stale skills."""
    card = AgentCard.create(name="TestAgent")

    # Add fresh skill
    fresh = Skill(name="python", confidence=0.9)
    card.add_skill(fresh)

    # Add stale skill
    stale = Skill(name="cobol", confidence=0.7)
    stale.last_used = datetime.now() - timedelta(days=100)
    card.add_skill(stale)

    # Age check
    stale_skills, metadata = card.age_check(stale_threshold_days=30)

    # Should flag stale skill
    assert len(stale_skills) == 1
    assert stale_skills[0].name == "cobol"
    assert metadata["stale_skills_count"] == 1
    assert metadata["freshness_score"] < 1.0
    assert metadata["needs_refresh"] is False  # Passport itself is fresh


def test_passport_age_check_in_export():
    """Test that age metadata is included in passport export."""
    card = AgentCard.create(name="TestAgent")

    # Add stale skill
    stale = Skill(name="fortran", confidence=0.5)
    stale.last_used = datetime.now() - timedelta(days=200)
    card.add_skill(stale)

    # Export
    card_dict = card.to_dict()

    # Should include age metadata
    assert "passport_age_days" in card_dict
    assert "stale_skills_count" in card_dict
    assert "freshness_score" in card_dict
    assert card_dict["stale_skills_count"] == 1


def test_passport_old_age_flags_refresh_needed():
    """Test that old passports flag as needing refresh."""
    card = AgentCard.create(name="TestAgent")

    # Artificially age the passport
    card.last_refreshed = datetime.now() - timedelta(days=90)

    _, metadata = card.age_check()

    # Should flag as needing refresh (>60 days)
    assert metadata["needs_refresh"] is True
    assert metadata["passport_age_days"] >= 90


def test_task_log_append_only_audit_trail():
    """Test that task log provides append-only audit trail."""
    task_log = TaskLog()

    # Add multiple tasks
    task_log.add(TaskEntry(
        task_id="task-1",
        description="Implement feature X",
        completed_at="2026-01-01T10:00:00",
        skill_used="python",
        outcome="success",
        feedback="good"
    ))

    task_log.add(TaskEntry(
        task_id="task-2",
        description="Fix bug Y",
        completed_at="2026-01-01T14:00:00",
        skill_used="debugging",
        outcome="success",
        feedback="good"
    ))

    task_log.add(TaskEntry(
        task_id="task-3",
        description="Implement feature Z",
        completed_at="2026-01-02T09:00:00",
        skill_used="javascript",
        outcome="failure",
        feedback="bad"
    ))

    # Reviewers can audit the actual work
    assert len(task_log.entries) == 3
    assert task_log.entries[0].task_id == "task-1"
    assert task_log.entries[2].outcome == "failure"

    # Stats provide summary
    stats = task_log.get_stats()
    assert stats["total"] == 3
    assert stats["success"] == 2
    assert stats["failure"] == 1
    assert stats["success_rate"] == 2/3


def test_task_log_skill_usage_tracking():
    """Test that task log tracks which skills were used."""
    task_log = TaskLog()

    task_log.add(TaskEntry("t1", "Task 1", "2026-01-01", "python", "success"))
    task_log.add(TaskEntry("t2", "Task 2", "2026-01-01", "python", "success"))
    task_log.add(TaskEntry("t3", "Task 3", "2026-01-01", "javascript", "failure"))

    stats = task_log.get_stats()

    # Can see which skills were actually used
    assert stats["skill_usage"]["python"] == 2
    assert stats["skill_usage"]["javascript"] == 1


def test_passport_includes_predictions_and_task_log():
    """Test that AgentCard includes both predictions and task log."""
    card = AgentCard.create(name="TestAgent")

    # Add prediction
    card.predictions = [
        {
            "statement": "Test prediction",
            "confidence": 0.8,
            "created_at": "2026-01-01",
            "deadline": "2026-12-31",
            "outcome": "confirmed"
        }
    ]

    # Add task log entry
    card.task_log = [
        {
            "task_id": "t1",
            "description": "Test task",
            "completed_at": "2026-01-01",
            "skill_used": "python",
            "outcome": "success",
            "feedback": "good"
        }
    ]

    # Export should include both
    card_dict = card.to_dict()
    assert len(card_dict["predictions"]) == 1
    assert len(card_dict["task_log"]) == 1


def test_skill_decay_with_low_stability():
    """Test that decayed_confidence accounts for staleness.

    A skill with high confidence but that hasn't been used in months
    should show lower decayed_confidence.
    """
    skill = Skill(
        name="python",
        confidence=0.9,
        fsrs_stability=2.0  # Low stability
    )

    # Age the skill
    skill.last_used = datetime.now() - timedelta(days=100)

    # Decayed confidence should be lower
    decayed = skill.decayed_confidence()

    # 100 days - 30 = 70 days = 10 weeks = 10% decay
    expected = 0.9 - 0.10
    assert abs(decayed - expected) < 0.01
    assert decayed < skill.confidence


def test_full_tamper_resistance_integration():
    """Integration test: all 4 tamper-resistance features work together."""
    card = AgentCard.create(name="TestAgent")

    # 1. Skills with FSRS data
    skill = Skill(
        name="python",
        confidence=0.85,
        evidence_count=100,
        fsrs_stability=7.5,
        fsrs_difficulty=6.0
    )
    card.add_skill(skill)

    # 2. Predictions with detail
    card.predictions = [
        {
            "statement": "Python will dominate AI",
            "confidence": 0.8,
            "created_at": "2026-01-01",
            "deadline": "2026-12-31",
            "outcome": "confirmed",
            "expected_outcome": "Market share > 50%",
            "actual_outcome": "Market share = 65%"
        }
    ]

    # 3. Age tracking
    stale_skills, metadata = card.age_check()
    assert metadata["passport_age_days"] >= 0

    # 4. Task log
    card.task_log = [
        {
            "task_id": "t1",
            "description": "Implement ML model",
            "completed_at": "2026-01-01",
            "skill_used": "python",
            "outcome": "success",
            "feedback": "good"
        }
    ]

    # Export should include all features
    card_dict = card.to_dict()

    assert card_dict["skills"][0]["fsrs_stability"] == 7.5
    assert card_dict["skills"][0]["fsrs_difficulty"] == 6.0
    assert "passport_age_days" in card_dict
    assert len(card_dict["predictions"]) == 1
    assert len(card_dict["task_log"]) == 1
    assert card_dict["predictions"][0]["expected_outcome"] is not None
    assert card_dict["task_log"][0]["skill_used"] == "python"
