"""Core AgentCard class - the passport itself."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import uuid

from .skills import Skill
from .reputation import Reputation


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
    skills: List[Skill] = field(default_factory=list)
    reputation: Optional[Reputation] = None
    task_history: TaskSummary = field(default_factory=TaskSummary)
    traits: Dict[str, str] = field(default_factory=dict)
    signature: Optional[str] = None

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "skills": [skill.to_dict() for skill in self.skills],
            "reputation": self.reputation.to_dict() if self.reputation else None,
            "task_history": self.task_history.to_dict(),
            "traits": self.traits,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Create from dictionary."""
        # Parse datetime strings
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])

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
            skills=skills,
            reputation=reputation,
            task_history=task_history,
            traits=data.get("traits", {}),
            signature=data.get("signature"),
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
