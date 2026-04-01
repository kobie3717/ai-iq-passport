"""Prediction tracking for auditable track record."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass
class Prediction:
    """A prediction with outcome tracking."""

    statement: str
    confidence: float
    created_at: str
    deadline: str
    outcome: str = "pending"  # "confirmed", "refuted", "pending"
    resolved_at: Optional[str] = None
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "statement": self.statement,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "outcome": self.outcome,
            "resolved_at": self.resolved_at,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prediction":
        """Create from dictionary."""
        return cls(
            statement=data["statement"],
            confidence=data.get("confidence", 0.5),
            created_at=data["created_at"],
            deadline=data["deadline"],
            outcome=data.get("outcome", "pending"),
            resolved_at=data.get("resolved_at"),
            expected_outcome=data.get("expected_outcome"),
            actual_outcome=data.get("actual_outcome"),
        )


class PredictionManager:
    """Manages predictions for auditable track record."""

    def __init__(self, predictions: Optional[List[Prediction]] = None):
        """Initialize prediction manager."""
        self.predictions: List[Prediction] = predictions or []

    def add(self, prediction: Prediction) -> None:
        """Add a new prediction."""
        self.predictions.append(prediction)

    def get_by_outcome(self, outcome: str) -> List[Prediction]:
        """Get predictions by outcome (confirmed/refuted/pending)."""
        return [p for p in self.predictions if p.outcome == outcome]

    def get_accuracy(self) -> float:
        """Calculate prediction accuracy (confirmed / total resolved)."""
        resolved = [p for p in self.predictions if p.outcome in ("confirmed", "refuted")]
        if not resolved:
            return 0.5

        confirmed = sum(1 for p in resolved if p.outcome == "confirmed")
        return confirmed / len(resolved)

    def get_stats(self) -> Dict[str, Any]:
        """Get prediction statistics."""
        total = len(self.predictions)
        confirmed = sum(1 for p in self.predictions if p.outcome == "confirmed")
        refuted = sum(1 for p in self.predictions if p.outcome == "refuted")
        pending = sum(1 for p in self.predictions if p.outcome == "pending")

        return {
            "total": total,
            "confirmed": confirmed,
            "refuted": refuted,
            "pending": pending,
            "accuracy": self.get_accuracy(),
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """Convert all predictions to list of dicts."""
        return [p.to_dict() for p in self.predictions]

    def import_from_ai_iq(self, db_path: str) -> int:
        """Import predictions from AI-IQ database.

        Args:
            db_path: Path to AI-IQ memories.db

        Returns:
            Number of predictions imported
        """
        try:
            import sqlite3
        except ImportError:
            raise ImportError("sqlite3 required for AI-IQ import")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        imported = 0

        # Check if predictions table exists
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        if 'predictions' in tables:
            cursor = conn.execute("""
                SELECT
                    prediction, confidence, deadline, expected_outcome,
                    actual_outcome, status, resolved_at, created_at
                FROM predictions
                ORDER BY created_at DESC
                LIMIT 100
            """)

            for row in cursor:
                # Map AI-IQ status to outcome
                status = row['status'] or "open"
                if status == "open":
                    outcome = "pending"
                elif status in ("confirmed", "refuted"):
                    outcome = status
                else:
                    outcome = "pending"

                pred = Prediction(
                    statement=row['prediction'],
                    confidence=row['confidence'] or 0.5,
                    created_at=row['created_at'],
                    deadline=row['deadline'] or row['created_at'],
                    outcome=outcome,
                    resolved_at=row['resolved_at'],
                    expected_outcome=row['expected_outcome'],
                    actual_outcome=row['actual_outcome'],
                )

                # Avoid duplicates
                if pred.to_dict() not in self.to_list():
                    self.predictions.append(pred)
                    imported += 1

        conn.close()
        return imported
