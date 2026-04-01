"""Core AgentCard class - the passport itself."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import json
import uuid

from .skills import Skill
from .reputation import Reputation
from .predictions import Prediction, PredictionManager
from .task_log import TaskEntry, TaskLog


@dataclass
class TaskSummary:
    """Summary of agent's task completion history."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    total_feedback_score: float = 0.0
    avg_feedback_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskSummary":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AgentCard:
    """The core passport object representing an AI agent's identity and reputation."""

    agent_id: str
    name: str
    version: str = "0.1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_refreshed: datetime = field(default_factory=datetime.now)
    skills: List[Skill] = field(default_factory=list)
    reputation: Optional[Reputation] = None
    task_history: TaskSummary = field(default_factory=TaskSummary)
    traits: Dict[str, str] = field(default_factory=dict)
    signature: Optional[str] = None
    predictions: List[Dict] = field(default_factory=list)
    task_log: List[Dict] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, agent_id: Optional[str] = None) -> "AgentCard":
        """Create a new agent card with generated ID."""
        if agent_id is None:
            agent_id = f"agent-{uuid.uuid4()}"

        return cls(agent_id=agent_id, name=name)

    def add_skill(self, skill: Skill) -> None:
        """Add or update a skill."""
        # Check if skill already exists
        for i, existing in enumerate(self.skills):
            if existing.name == skill.name:
                self.skills[i] = skill
                self.updated_at = datetime.now()
                return

        # Add new skill
        self.skills.append(skill)
        self.updated_at = datetime.now()

    def remove_skill(self, skill_name: str) -> bool:
        """Remove a skill by name. Returns True if removed."""
        for i, skill in enumerate(self.skills):
            if skill.name == skill_name:
                del self.skills[i]
                self.updated_at = datetime.now()
                return True
        return False

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name."""
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def add_trait(self, key: str, value: str) -> None:
        """Add or update a trait."""
        self.traits[key] = value
        self.updated_at = datetime.now()

    def age_days(self) -> int:
        """Days since passport was last refreshed."""
        return (datetime.now() - self.last_refreshed).days

    def age_check(self, stale_threshold_days: int = 30) -> Tuple[List[Skill], Dict[str, Any]]:
        """Check which skills are stale and passport freshness.

        Args:
            stale_threshold_days: Days after which a skill is considered stale

        Returns:
            Tuple of (stale_skills_list, metadata_dict)
        """
        stale_skills = [s for s in self.skills if s.is_stale(stale_threshold_days)]

        metadata = {
            "passport_age_days": self.age_days(),
            "stale_skills_count": len(stale_skills),
            "total_skills": len(self.skills),
            "freshness_score": 1.0 - (len(stale_skills) / len(self.skills)) if self.skills else 1.0,
            "needs_refresh": self.age_days() > 60,
        }

        return stale_skills, metadata

    def refresh(self) -> None:
        """Mark passport as refreshed (updates last_refreshed timestamp)."""
        self.last_refreshed = datetime.now()
        self.updated_at = datetime.now()

    def log_task(self, task: str, outcome: str, tags: List[str]) -> None:
        """Log a task (append-only).

        Args:
            task: Task description
            outcome: "success" or "failure"
            tags: List of tags for categorization
        """
        self.task_log.append({
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "outcome": outcome,
            "tags": tags
        })
        self.updated_at = datetime.now()

    def task_stats(self) -> Dict[str, Any]:
        """Get statistics from task log.

        Returns:
            Dict with total, success_count, failure_count, success_rate, tags_distribution
        """
        if not self.task_log:
            return {
                "total": 0,
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "tags_distribution": {}
            }

        total = len(self.task_log)
        success_count = sum(1 for t in self.task_log if t["outcome"] == "success")
        failure_count = sum(1 for t in self.task_log if t["outcome"] == "failure")

        # Count tag occurrences
        tags_distribution = {}
        for task in self.task_log:
            for tag in task.get("tags", []):
                tags_distribution[tag] = tags_distribution.get(tag, 0) + 1

        return {
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / total if total > 0 else 0.0,
            "tags_distribution": tags_distribution
        }

    def import_ai_iq_data(self, db_path: str) -> Dict[str, int]:
        """Import predictions and task logs from AI-IQ database.

        Args:
            db_path: Path to AI-IQ memories.db

        Returns:
            Dict with counts of imported items
        """
        # Use PredictionManager and TaskLog for structured import
        pred_manager = PredictionManager()
        task_log = TaskLog()

        # Import using dedicated managers
        pred_count = pred_manager.import_from_ai_iq(db_path)
        task_count = task_log.import_from_ai_iq(db_path)

        # Convert predictions to dicts for storage
        self.predictions = pred_manager.to_list()

        # Convert task log entries to card's simple format
        # TaskEntry has: task_id, description, completed_at, skill_used, outcome, feedback
        # Card format needs: task, timestamp, outcome, tags
        for entry_dict in task_log.to_list():
            normalized = {
                "task": entry_dict["description"],
                "timestamp": entry_dict["completed_at"],
                "outcome": entry_dict["outcome"],
                "tags": [entry_dict["skill_used"]] if entry_dict["skill_used"] else []
            }
            self.task_log.append(normalized)

        self.updated_at = datetime.now()
        self.last_refreshed = datetime.now()

        return {"predictions": pred_count, "tasks": task_count}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Get age check metadata
        _, age_metadata = self.age_check()

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_refreshed": self.last_refreshed.isoformat(),
            "passport_age_days": age_metadata["passport_age_days"],
            "stale_skills_count": age_metadata["stale_skills_count"],
            "freshness_score": age_metadata["freshness_score"],
            "skills": [skill.to_dict() for skill in self.skills],
            "reputation": self.reputation.to_dict() if self.reputation else None,
            "task_history": self.task_history.to_dict(),
            "traits": self.traits,
            "signature": self.signature,
            "predictions": self.predictions,
            "task_log": self.task_log,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Create from dictionary."""
        # Parse datetime strings
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])

        # Parse last_refreshed (backward compatible - defaults to updated_at)
        last_refreshed = updated_at
        if data.get("last_refreshed"):
            last_refreshed = datetime.fromisoformat(data["last_refreshed"])

        # Parse skills
        skills = [Skill.from_dict(s) for s in data.get("skills", [])]

        # Parse reputation
        reputation = None
        if data.get("reputation"):
            reputation = Reputation.from_dict(data["reputation"])

        # Parse task history
        task_history = TaskSummary.from_dict(
            data.get("task_history", {})
        ) if data.get("task_history") else TaskSummary()

        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            version=data.get("version", "0.1.0"),
            created_at=created_at,
            updated_at=updated_at,
            last_refreshed=last_refreshed,
            skills=skills,
            reputation=reputation,
            task_history=task_history,
            traits=data.get("traits", {}),
            signature=data.get("signature"),
            predictions=data.get("predictions", []),
            task_log=data.get("task_log", []),
        )

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentCard":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, filepath: str) -> None:
        """Save to JSON file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "AgentCard":
        """Load from JSON file."""
        with open(filepath, "r") as f:
            return cls.from_json(f.read())

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"Agent: {self.name} ({self.agent_id})",
            f"Version: {self.version}",
            f"Created: {self.created_at.strftime('%Y-%m-%d')}",
            f"Updated: {self.updated_at.strftime('%Y-%m-%d')}",
            "",
            f"Skills ({len(self.skills)}):",
        ]

        # Sort skills by confidence
        sorted_skills = sorted(self.skills, key=lambda s: s.confidence, reverse=True)
        for skill in sorted_skills[:10]:  # Top 10
            lines.append(
                f"  - {skill.name}: {skill.confidence:.2f} "
                f"({skill.evidence_count} tasks)"
            )

        if len(self.skills) > 10:
            lines.append(f"  ... and {len(self.skills) - 10} more")

        if self.reputation:
            lines.append("")
            lines.append(f"Reputation: {self.reputation.overall_score:.2f}")
            lines.append(f"  - Feedback: {self.reputation.feedback_score:.2f}")
            lines.append(f"  - Prediction accuracy: {self.reputation.prediction_accuracy:.2f}")
            lines.append(f"  - Task completion: {self.reputation.task_completion_rate:.2f}")

        if self.task_history.total_tasks > 0:
            lines.append("")
            lines.append(f"Tasks: {self.task_history.completed_tasks}/{self.task_history.total_tasks} completed")
            lines.append(f"Success rate: {self.task_history.success_rate:.1%}")

        if self.traits:
            lines.append("")
            lines.append("Traits:")
            for key, value in self.traits.items():
                lines.append(f"  - {key}: {value}")

        if self.signature:
            lines.append("")
            lines.append(f"Signed: {self.signature[:32]}...")

        return "\n".join(lines)
