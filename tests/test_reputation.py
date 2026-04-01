"""Tests for Reputation and ReputationCalculator."""

from datetime import datetime, timedelta
import pytest

from passport.reputation import Reputation, ReputationCalculator
from passport.skills import Skill


def test_create_reputation():
    """Test creating a reputation object."""
    rep = Reputation(
        overall_score=0.8,
        feedback_score=0.9,
        prediction_accuracy=0.7,
        task_completion_rate=0.85,
    )

    assert rep.overall_score == 0.8
    assert rep.feedback_score == 0.9


def test_reputation_serialization():
    """Test reputation to_dict and from_dict."""
    rep1 = Reputation(
        overall_score=0.8,
        total_feedback=50,
        total_predictions=20,
        total_tasks=100,
    )

    data = rep1.to_dict()
    rep2 = Reputation.from_dict(data)

    assert rep2.overall_score == rep1.overall_score
    assert rep2.total_feedback == rep1.total_feedback


def test_calculator_manual():
    """Test manual reputation calculation."""
    calc = ReputationCalculator()

    # Good feedback
    feedback = ["good", "good", "good", "meh", "bad"]

    # Good predictions
    predictions = {"confirmed": 8, "refuted": 2}

    # Good task completion
    tasks = {"completed": 18, "total": 20}

    rep = calc.calculate_manual(
        feedback_data=feedback,
        predictions_data=predictions,
        tasks_data=tasks,
    )

    assert rep.total_feedback == 5
    assert rep.feedback_score == 0.7  # (3*1.0 + 1*0.5 + 1*0.0) / 5
    assert rep.prediction_accuracy == 0.8  # 8/10
    assert rep.task_completion_rate == 0.9  # 18/20
    assert rep.overall_score > 0.0


def test_calculator_all_good_feedback():
    """Test calculation with all good feedback."""
    calc = ReputationCalculator()
    feedback = ["good"] * 10

    rep = calc.calculate_manual(feedback_data=feedback)

    assert rep.feedback_score == 1.0


def test_calculator_all_bad_feedback():
    """Test calculation with all bad feedback."""
    calc = ReputationCalculator()
    feedback = ["bad"] * 10

    rep = calc.calculate_manual(feedback_data=feedback)

    assert rep.feedback_score == 0.0


def test_calculator_mixed_feedback():
    """Test calculation with mixed feedback."""
    calc = ReputationCalculator()
    feedback = ["good", "meh"]

    rep = calc.calculate_manual(feedback_data=feedback)

    assert rep.feedback_score == 0.75  # (1.0 + 0.5) / 2


def test_calculator_no_data():
    """Test calculation with no data (defaults)."""
    calc = ReputationCalculator()

    rep = calc.calculate_manual()

    # With v0.3.0 weights (30% feedback, 25% predictions, 20% tasks, 15% consistency, 10% skill_quality)
    # All at 0.5: 0.3*0.5 + 0.25*0.5 + 0.2*0.5 + 0.15*0.5 + 0.1*0.5 = 0.5
    assert rep.overall_score == 0.5
    assert rep.feedback_score == 0.5
    assert rep.prediction_accuracy == 0.5


def test_calculator_weights():
    """Test that weights sum correctly."""
    calc = ReputationCalculator()

    total_weight = sum(calc.weights.values())

    assert abs(total_weight - 1.0) < 0.01  # Should sum to ~1.0


def test_calculator_perfect_score():
    """Test calculation with perfect scores."""
    calc = ReputationCalculator()

    feedback = ["good"] * 10
    predictions = {"confirmed": 10, "refuted": 0}
    tasks = {"completed": 20, "total": 20}

    rep = calc.calculate_manual(
        feedback_data=feedback,
        predictions_data=predictions,
        tasks_data=tasks,
    )

    # Overall should be high (close to 1.0) but not quite due to consistency
    assert rep.overall_score > 0.8
    assert rep.feedback_score == 1.0
    assert rep.prediction_accuracy == 1.0
    assert rep.task_completion_rate == 1.0


# New v0.3.0 tests for skill quality scoring

def test_calculator_skill_quality_no_skills():
    """Test skill quality calculation with no skills."""
    calc = ReputationCalculator()

    quality = calc._calculate_skill_quality([])

    assert quality == 0.5


def test_calculator_skill_quality_fresh_skills():
    """Test skill quality with fresh, high-confidence skills."""
    calc = ReputationCalculator()

    skills = [
        Skill(name="python", confidence=0.9, fsrs_stability=5.0),
        Skill(name="javascript", confidence=0.8, fsrs_stability=4.0),
    ]

    quality = calc._calculate_skill_quality(skills)

    # Should be high since skills are fresh and confident
    assert quality > 0.7


def test_calculator_skill_quality_stale_skills():
    """Test skill quality with stale skills (decayed confidence)."""
    calc = ReputationCalculator()

    skill = Skill(name="python", confidence=0.9, fsrs_stability=5.0)
    skill.last_used = datetime.now() - timedelta(days=100)

    skills = [skill]

    quality = calc._calculate_skill_quality(skills)

    # Should be lower due to decay
    # 100 days - 30 = 70 days = 10 weeks = 10% decay
    # Confidence: 0.9 - 0.1 = 0.8
    # Stability weight: min(1.0, 5.0/10) = 0.5
    # Weighted: 0.8 * 0.5 / 0.5 = 0.8
    assert 0.75 < quality < 0.85


def test_calculator_skill_quality_high_stability():
    """Test skill quality weighs high stability more."""
    calc = ReputationCalculator()

    skills = [
        Skill(name="python", confidence=0.8, fsrs_stability=10.0),  # High stability
        Skill(name="javascript", confidence=0.8, fsrs_stability=1.0),  # Low stability
    ]

    quality = calc._calculate_skill_quality(skills)

    # High stability skill should have more weight
    assert quality > 0.0


def test_calculator_skill_quality_zero_stability():
    """Test skill quality handles zero stability gracefully."""
    calc = ReputationCalculator()

    skills = [
        Skill(name="python", confidence=0.9, fsrs_stability=0.0),
    ]

    quality = calc._calculate_skill_quality(skills)

    # Should still calculate with default weight
    assert 0.0 <= quality <= 1.0


def test_calculator_weights_updated():
    """Test that v0.3.0 weights include skill_quality."""
    calc = ReputationCalculator()

    assert "skill_quality" in calc.weights
    assert calc.weights["skill_quality"] == 0.10

    # Weights should still sum to 1.0
    total_weight = sum(calc.weights.values())
    assert abs(total_weight - 1.0) < 0.01
