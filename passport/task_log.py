"""Task log for append-only audit trail."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any


@dataclass
class TaskEntry:
    """A single task entry in the audit log."""

    task_id: str
    description: str
    completed_at: str
    skill_used: str
    outcome: str  # "success", "failure", "partial"
    feedback: Optional[str] = None  # "good", "bad", "meh"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "completed_at": self.completed_at,
            "skill_used": self.skill_used,
            "outcome": self.outcome,
            "feedback": self.feedback,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskEntry":
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            description=data["description"],
            completed_at=data["completed_at"],
            skill_used=data["skill_used"],
            outcome=data["outcome"],
            feedback=data.get("feedback"),
        )


class TaskLog:
    """Manages append-only task audit trail."""

    def __init__(self, entries: Optional[List[TaskEntry]] = None):
        """Initialize task log."""
        self.entries: List[TaskEntry] = entries or []

    def add(self, entry: TaskEntry) -> None:
        """Add a new task entry (append-only)."""
        self.entries.append(entry)

    def get_by_outcome(self, outcome: str) -> List[TaskEntry]:
        """Get tasks by outcome (success/failure/partial)."""
        return [e for e in self.entries if e.outcome == outcome]

    def get_by_skill(self, skill: str) -> List[TaskEntry]:
        """Get tasks by skill used."""
        return [e for e in self.entries if e.skill_used == skill]

    def get_success_rate(self) -> float:
        """Calculate overall success rate."""
        if not self.entries:
            return 0.5

        successes = sum(1 for e in self.entries if e.outcome == "success")
        return successes / len(self.entries)

    def get_stats(self) -> Dict[str, Any]:
        """Get task log statistics."""
        total = len(self.entries)
        success = sum(1 for e in self.entries if e.outcome == "success")
        failure = sum(1 for e in self.entries if e.outcome == "failure")
        partial = sum(1 for e in self.entries if e.outcome == "partial")

        # Feedback stats
        good = sum(1 for e in self.entries if e.feedback == "good")
        bad = sum(1 for e in self.entries if e.feedback == "bad")
        meh = sum(1 for e in self.entries if e.feedback == "meh")

        # Skill usage distribution
        skill_usage = {}
        for entry in self.entries:
            skill_usage[entry.skill_used] = skill_usage.get(entry.skill_used, 0) + 1

        return {
            "total": total,
            "success": success,
            "failure": failure,
            "partial": partial,
            "success_rate": self.get_success_rate(),
            "feedback": {
                "good": good,
                "bad": bad,
                "meh": meh,
            },
            "skill_usage": skill_usage,
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """Convert all entries to list of dicts."""
        return [e.to_dict() for e in self.entries]

    def import_from_ai_iq(self, db_path: str) -> int:
        """Import task entries from AI-IQ database.

        Imports from:
        - feedback table (with linked memories)
        - memories with category='project'

        Args:
            db_path: Path to AI-IQ memories.db

        Returns:
            Number of task entries imported
        """
        try:
            import sqlite3
        except ImportError:
            raise ImportError("sqlite3 required for AI-IQ import")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        imported = 0

        # Check which tables exist
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        # Import from feedback table
        if 'feedback' in tables:
            cursor = conn.execute("""
                SELECT f.rating, f.reason, f.session_id, f.created_at, f.linked_memory_id,
                       m.content, m.tags
                FROM feedback f
                LEFT JOIN memories m ON f.linked_memory_id = m.id
                ORDER BY f.created_at DESC
                LIMIT 200
            """)

            for row in cursor:
                # Map rating to outcome
                rating = row['rating']
                if rating == 'good':
                    outcome = "success"
                elif rating == 'bad':
                    outcome = "failure"
                else:
                    outcome = "partial"

                # Extract skill from tags or default to 'general'
                skill_used = "general"
                if row['tags']:
                    tags = row['tags'].split(',')
                    skill_used = tags[0].strip() if tags else "general"

                # Generate task ID from session and timestamp
                task_id = f"{row['session_id'] or 'unknown'}-{row['created_at']}"

                description = row['reason'] or row['content'] or "Task completed"

                entry = TaskEntry(
                    task_id=task_id,
                    description=description[:200],  # Truncate long descriptions
                    completed_at=row['created_at'],
                    skill_used=skill_used,
                    outcome=outcome,
                    feedback=rating,
                )

                # Avoid duplicates
                if entry.to_dict() not in self.to_list():
                    self.entries.append(entry)
                    imported += 1

        # Import from project memories
        if 'memories' in tables:
            cursor = conn.execute("""
                SELECT id, content, tags, created_at, updated_at
                FROM memories
                WHERE category = 'project' AND active = 1
                ORDER BY created_at DESC
                LIMIT 100
            """)

            for row in cursor:
                # Infer outcome from content
                content = row['content'] or ""
                outcome = "success"  # Default to success

                if any(word in content.lower() for word in ['error', 'failed', 'bug', 'fix']):
                    outcome = "failure"
                elif any(word in content.lower() for word in ['partial', 'wip', 'incomplete']):
                    outcome = "partial"

                # Extract skill from tags
                skill_used = "general"
                if row['tags']:
                    tags = row['tags'].split(',')
                    skill_used = tags[0].strip() if tags else "general"

                task_id = f"project-{row['id']}"

                entry = TaskEntry(
                    task_id=task_id,
                    description=content[:200],
                    completed_at=row['updated_at'] or row['created_at'],
                    skill_used=skill_used,
                    outcome=outcome,
                    feedback=None,
                )

                # Avoid duplicates
                if entry.to_dict() not in self.to_list():
                    self.entries.append(entry)
                    imported += 1

        conn.close()
        return imported
