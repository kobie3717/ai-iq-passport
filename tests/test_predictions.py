"""Tests for Prediction and PredictionManager."""

from datetime import datetime
import pytest

from passport.predictions import Prediction, PredictionManager


def test_create_prediction():
    """Test creating a prediction."""
    pred = Prediction(
        statement="Python will dominate AI in 2026",
        confidence=0.8,
        created_at="2026-01-01",
        deadline="2026-12-31",
        outcome="pending"
    )

    assert pred.statement == "Python will dominate AI in 2026"
    assert pred.confidence == 0.8
    assert pred.outcome == "pending"


def test_prediction_serialization():
    """Test prediction to_dict and from_dict."""
    pred1 = Prediction(
        statement="Test prediction",
        confidence=0.7,
        created_at="2026-01-01",
        deadline="2026-12-31",
        outcome="confirmed",
        resolved_at="2026-06-15"
    )

    data = pred1.to_dict()
    pred2 = Prediction.from_dict(data)

    assert pred2.statement == pred1.statement
    assert pred2.confidence == pred1.confidence
    assert pred2.outcome == pred1.outcome
    assert pred2.resolved_at == pred1.resolved_at


def test_prediction_manager_add():
    """Test adding predictions to manager."""
    manager = PredictionManager()

    pred = Prediction(
        statement="Test",
        confidence=0.8,
        created_at="2026-01-01",
        deadline="2026-12-31"
    )

    manager.add(pred)

    assert len(manager.predictions) == 1


def test_prediction_manager_get_by_outcome():
    """Test filtering predictions by outcome."""
    manager = PredictionManager()

    pred1 = Prediction("Test 1", 0.8, "2026-01-01", "2026-12-31", outcome="confirmed")
    pred2 = Prediction("Test 2", 0.7, "2026-01-01", "2026-12-31", outcome="refuted")
    pred3 = Prediction("Test 3", 0.9, "2026-01-01", "2026-12-31", outcome="pending")

    manager.add(pred1)
    manager.add(pred2)
    manager.add(pred3)

    confirmed = manager.get_by_outcome("confirmed")
    refuted = manager.get_by_outcome("refuted")
    pending = manager.get_by_outcome("pending")

    assert len(confirmed) == 1
    assert len(refuted) == 1
    assert len(pending) == 1


def test_prediction_manager_accuracy():
    """Test accuracy calculation."""
    manager = PredictionManager()

    # 3 confirmed, 1 refuted = 75% accuracy
    manager.add(Prediction("P1", 0.8, "2026-01-01", "2026-12-31", outcome="confirmed"))
    manager.add(Prediction("P2", 0.8, "2026-01-01", "2026-12-31", outcome="confirmed"))
    manager.add(Prediction("P3", 0.8, "2026-01-01", "2026-12-31", outcome="confirmed"))
    manager.add(Prediction("P4", 0.8, "2026-01-01", "2026-12-31", outcome="refuted"))
    manager.add(Prediction("P5", 0.8, "2026-01-01", "2026-12-31", outcome="pending"))

    accuracy = manager.get_accuracy()

    assert accuracy == 0.75


def test_prediction_manager_accuracy_no_resolved():
    """Test accuracy with no resolved predictions."""
    manager = PredictionManager()

    manager.add(Prediction("P1", 0.8, "2026-01-01", "2026-12-31", outcome="pending"))

    accuracy = manager.get_accuracy()

    assert accuracy == 0.5  # Default when no data


def test_prediction_manager_stats():
    """Test getting prediction statistics."""
    manager = PredictionManager()

    manager.add(Prediction("P1", 0.8, "2026-01-01", "2026-12-31", outcome="confirmed"))
    manager.add(Prediction("P2", 0.8, "2026-01-01", "2026-12-31", outcome="confirmed"))
    manager.add(Prediction("P3", 0.8, "2026-01-01", "2026-12-31", outcome="refuted"))
    manager.add(Prediction("P4", 0.8, "2026-01-01", "2026-12-31", outcome="pending"))

    stats = manager.get_stats()

    assert stats["total"] == 4
    assert stats["confirmed"] == 2
    assert stats["refuted"] == 1
    assert stats["pending"] == 1
    assert stats["accuracy"] > 0.0


def test_prediction_manager_to_list():
    """Test converting predictions to list."""
    manager = PredictionManager()

    manager.add(Prediction("P1", 0.8, "2026-01-01", "2026-12-31"))

    pred_list = manager.to_list()

    assert len(pred_list) == 1
    assert isinstance(pred_list[0], dict)
    assert pred_list[0]["statement"] == "P1"
