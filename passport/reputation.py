"""Reputation scoring from feedback and predictions."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple


@dataclass
class Reputation:
    """Overall reputation score with breakdown."""

    overall_score: float = 0.5
    feedback_score: float = 0.5
    prediction_accuracy: float = 0.5
    task_completion_rate: float = 0.5
    consistency_score: float = 0.5
    total_feedback: int = 0
    total_predictions: int = 0
    total_tasks: int = 0
    last_calculated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "feedback_score": self.feedback_score,
            "prediction_accuracy": self.prediction_accuracy,
            "task_completion_rate": self.task_completion_rate,
            "consistency_score": self.consistency_score,
            "total_feedback": self.total_feedback,
            "total_predictions": self.total_predictions,
            "total_tasks": self.total_tasks,
            "last_calculated": self.last_calculated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reputation":
        """Create from dictionary."""
        last_calculated = datetime.fromisoformat(data["last_calculated"])
        return cls(
            overall_score=data.get("overall_score", 0.5),
            feedback_score=data.get("feedback_score", 0.5),
            prediction_accuracy=data.get("prediction_accuracy", 0.5),
            task_completion_rate=data.get("task_completion_rate", 0.5),
            consistency_score=data.get("consistency_score", 0.5),
            total_feedback=data.get("total_feedback", 0),
            total_predictions=data.get("total_predictions", 0),
            total_tasks=data.get("total_tasks", 0),
            last_calculated=last_calculated,
        )


class ReputationCalculator:
    """Calculates reputation from various sources."""

    def __init__(self):
        """Initialize reputation calculator."""
        self.weights = {
            "feedback": 0.30,
            "predictions": 0.25,
            "tasks": 0.20,
            "consistency": 0.15,
            "skill_quality": 0.10,
        }

    def calculate_from_ai_iq(self, db_path: str, skills: List = None) -> Reputation:
        """Calculate reputation from AI-IQ database.

        Args:
            db_path: Path to AI-IQ memories.db
            skills: Optional list of Skill objects to factor into quality score

        Returns:
            Reputation object with calculated scores
        """
        try:
            import sqlite3
        except ImportError:
            raise ImportError("sqlite3 required for AI-IQ import")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Calculate feedback score
        feedback_score, total_feedback = self._calculate_feedback_score(conn)

        # Calculate prediction accuracy
        prediction_accuracy, total_predictions = self._calculate_prediction_accuracy(conn)

        # Calculate task completion rate
        task_completion, total_tasks = self._calculate_task_completion(conn)

        # Calculate consistency score
        consistency = self._calculate_consistency(conn)

        # Calculate skill quality score (uses decayed confidence)
        skill_quality = self._calculate_skill_quality(skills) if skills else 0.5

        # Calculate weighted overall score
        overall = (
            feedback_score * self.weights["feedback"]
            + prediction_accuracy * self.weights["predictions"]
            + task_completion * self.weights["tasks"]
            + consistency * self.weights["consistency"]
            + skill_quality * self.weights["skill_quality"]
        )

        conn.close()

        return Reputation(
            overall_score=overall,
            feedback_score=feedback_score,
            prediction_accuracy=prediction_accuracy,
            task_completion_rate=task_completion,
            consistency_score=consistency,
            total_feedback=total_feedback,
            total_predictions=total_predictions,
            total_tasks=total_tasks,
            last_calculated=datetime.now(),
        )

    def _calculate_feedback_score(self, conn) -> Tuple[float, int]:
        """Calculate score from feedback table (good/bad/meh ratio).

        Returns:
            (score 0.0-1.0, total_feedback_count)
        """
        try:
            cursor = conn.execute("""
                SELECT feedback, COUNT(*) as count
                FROM feedback
                GROUP BY feedback
            """)

            feedback_counts = {"good": 0, "bad": 0, "meh": 0}
            for row in cursor:
                feedback_type = row['feedback']
                if feedback_type in feedback_counts:
                    feedback_counts[feedback_type] = row['count']

            total = sum(feedback_counts.values())
            if total == 0:
                return 0.5, 0

            # Good = 1.0, Meh = 0.5, Bad = 0.0
            score = (
                feedback_counts["good"] * 1.0
                + feedback_counts["meh"] * 0.5
                + feedback_counts["bad"] * 0.0
            ) / total

            return score, total

        except Exception:
            return 0.5, 0

    def _calculate_prediction_accuracy(self, conn) -> Tuple[float, int]:
        """Calculate accuracy from predictions table (confirmed vs refuted).

        Returns:
            (accuracy 0.0-1.0, total_predictions)
        """
        try:
            cursor = conn.execute("""
                SELECT outcome, COUNT(*) as count
                FROM predictions
                WHERE outcome IS NOT NULL
                GROUP BY outcome
            """)

            outcomes = {"confirmed": 0, "refuted": 0}
            for row in cursor:
                outcome = row['outcome']
                if outcome in outcomes:
                    outcomes[outcome] = row['count']

            total = sum(outcomes.values())
            if total == 0:
                return 0.5, 0

            accuracy = outcomes["confirmed"] / total
            return accuracy, total

        except Exception:
            return 0.5, 0

    def _calculate_task_completion(self, conn) -> Tuple[float, int]:
        """Calculate task completion rate from memories.

        Looks for pending memories and their resolution.

        Returns:
            (completion_rate 0.0-1.0, total_tasks)
        """
        try:
            # Count completed tasks (pending memories that were deleted)
            # This is tricky - we can look at memories with category='pending'
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM memories
                WHERE category = 'pending' AND deleted = 0
            """)
            pending = cursor.fetchone()['count'] or 0

            # Estimate completed tasks from expired pending items
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM memories
                WHERE category = 'pending' AND deleted = 1
            """)
            completed = cursor.fetchone()['count'] or 0

            total = pending + completed
            if total == 0:
                return 0.5, 0

            completion_rate = completed / total
            return completion_rate, total

        except Exception:
            return 0.5, 0

    def _calculate_consistency(self, conn) -> float:
        """Calculate consistency score based on activity patterns.

        More consistent activity over time = higher score.

        Returns:
            consistency score 0.0-1.0
        """
        try:
            # Get activity distribution over last 90 days
            ninety_days_ago = (datetime.now() - timedelta(days=90)).isoformat()

            cursor = conn.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM memories
                WHERE created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (ninety_days_ago,))

            daily_counts = [row['count'] for row in cursor]

            if len(daily_counts) == 0:
                return 0.5

            # Calculate coefficient of variation (lower = more consistent)
            mean = sum(daily_counts) / len(daily_counts)
            if mean == 0:
                return 0.5

            variance = sum((x - mean) ** 2 for x in daily_counts) / len(daily_counts)
            std_dev = variance ** 0.5
            cv = std_dev / mean

            # Convert CV to 0-1 score (lower CV = higher consistency)
            # CV > 2.0 is very inconsistent, CV < 0.5 is very consistent
            consistency = max(0.0, min(1.0, 1.0 - (cv / 2.0)))
            return consistency

        except Exception:
            return 0.5

    def _calculate_skill_quality(self, skills: List) -> float:
        """Calculate skill quality score from skills with FSRS stability.

        Uses decayed_confidence to account for staleness.

        Args:
            skills: List of Skill objects

        Returns:
            quality score 0.0-1.0
        """
        if not skills:
            return 0.5

        # Calculate average decayed confidence weighted by FSRS stability
        total_weighted_confidence = 0.0
        total_weight = 0.0

        for skill in skills:
            # Use decayed confidence to account for staleness
            decayed_conf = skill.decayed_confidence()

            # Weight by FSRS stability (higher stability = more reliable)
            # Stability typically ranges 0.1 to 10+, normalize to 0-1
            stability_weight = min(1.0, skill.fsrs_stability / 10.0) if skill.fsrs_stability > 0 else 0.5

            # Combine confidence and stability
            weighted_conf = decayed_conf * stability_weight

            total_weighted_confidence += weighted_conf
            total_weight += stability_weight

        if total_weight == 0:
            return 0.5

        avg_quality = total_weighted_confidence / total_weight
        return avg_quality

    def calculate_manual(
        self,
        feedback_data: Optional[List[str]] = None,
        predictions_data: Optional[Dict[str, int]] = None,
        tasks_data: Optional[Dict[str, int]] = None,
        skills: List = None,
    ) -> Reputation:
        """Calculate reputation from manually provided data.

        Args:
            feedback_data: List of feedback strings ("good", "bad", "meh")
            predictions_data: Dict with "confirmed" and "refuted" counts
            tasks_data: Dict with "completed" and "total" counts
            skills: Optional list of Skill objects

        Returns:
            Reputation object
        """
        feedback_score = 0.5
        total_feedback = 0
        if feedback_data:
            good = feedback_data.count("good")
            bad = feedback_data.count("bad")
            meh = feedback_data.count("meh")
            total_feedback = len(feedback_data)
            if total_feedback > 0:
                feedback_score = (good * 1.0 + meh * 0.5) / total_feedback

        prediction_accuracy = 0.5
        total_predictions = 0
        if predictions_data:
            confirmed = predictions_data.get("confirmed", 0)
            refuted = predictions_data.get("refuted", 0)
            total_predictions = confirmed + refuted
            if total_predictions > 0:
                prediction_accuracy = confirmed / total_predictions

        task_completion = 0.5
        total_tasks = 0
        if tasks_data:
            completed = tasks_data.get("completed", 0)
            total_tasks = tasks_data.get("total", 0)
            if total_tasks > 0:
                task_completion = completed / total_tasks

        # Simple consistency (no data available for manual mode)
        consistency = 0.5

        # Calculate skill quality if skills provided
        skill_quality = self._calculate_skill_quality(skills) if skills else 0.5

        overall = (
            feedback_score * self.weights["feedback"]
            + prediction_accuracy * self.weights["predictions"]
            + task_completion * self.weights["tasks"]
            + consistency * self.weights["consistency"]
            + skill_quality * self.weights["skill_quality"]
        )

        return Reputation(
            overall_score=overall,
            feedback_score=feedback_score,
            prediction_accuracy=prediction_accuracy,
            task_completion_rate=task_completion,
            consistency_score=consistency,
            total_feedback=total_feedback,
            total_predictions=total_predictions,
            total_tasks=total_tasks,
            last_calculated=datetime.now(),
        )
