"""Tests for Reputation and ReputationCalculator."""

from datetime import datetime
import pytest

from passport.reputation import Reputation, ReputationCalculator


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
