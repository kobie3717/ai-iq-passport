"""Skill tracking with confidence and evidence."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class Skill:
    """Represents a skill with confidence and evidence."""

    name: str
    confidence: float = 0.5
    evidence_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence range."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "last_used": self.last_used.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create from dictionary."""
        last_used = datetime.fromisoformat(data["last_used"])
        return cls(
            name=data["name"],
            confidence=data.get("confidence", 0.5),
            evidence_count=data.get("evidence_count", 0),
            last_used=last_used,
            tags=data.get("tags", []),
        )

    def boost(self, amount: float = 0.1) -> None:
        """Increase confidence by amount."""
        self.confidence = min(1.0, self.confidence + amount)
        self.evidence_count += 1
        self.last_used = datetime.now()

    def decay(self, amount: float = 0.05) -> None:
        """Decrease confidence by amount (e.g., due to inactivity)."""
        self.confidence = max(0.0, self.confidence - amount)


class SkillManager:
    """Manages skills for an agent, with decay and evidence tracking."""

    def __init__(self, skills: Optional[List[Skill]] = None):
        """Initialize skill manager."""
        self.skills: Dict[str, Skill] = {}
        if skills:
            for skill in skills:
                self.skills[skill.name] = skill

    def add_or_update(self, skill: Skill) -> None:
        """Add a new skill or update existing one."""
        self.skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        """Get skill by name."""
        return self.skills.get(name)

    def remove(self, name: str) -> bool:
        """Remove skill by name. Returns True if removed."""
        if name in self.skills:
            del self.skills[name]
            return True
        return False

    def boost_skill(self, name: str, amount: float = 0.1) -> bool:
        """Boost confidence for a skill. Creates it if not exists."""
        if name not in self.skills:
            self.skills[name] = Skill(name=name, confidence=0.5)

        self.skills[name].boost(amount)
        return True

    def record_usage(self, name: str, success: bool = True) -> None:
        """Record skill usage with success/failure."""
        if name not in self.skills:
            self.skills[name] = Skill(name=name, confidence=0.5)

        skill = self.skills[name]
        if success:
            skill.boost(0.05)
        else:
            skill.decay(0.1)

    def decay_unused(self, days_threshold: int = 90, decay_amount: float = 0.05) -> int:
        """Decay skills not used in X days. Returns count of decayed skills."""
        now = datetime.now()
        decayed_count = 0

        for skill in self.skills.values():
            days_since_use = (now - skill.last_used).days
            if days_since_use > days_threshold:
                skill.decay(decay_amount)
                decayed_count += 1

        return decayed_count

    def get_top_skills(self, n: int = 10) -> List[Skill]:
        """Get top N skills by confidence."""
        sorted_skills = sorted(
            self.skills.values(),
            key=lambda s: (s.confidence, s.evidence_count),
            reverse=True
        )
        return sorted_skills[:n]

    def get_skills_by_tag(self, tag: str) -> List[Skill]:
        """Get all skills with a specific tag."""
        return [s for s in self.skills.values() if tag in s.tags]

    def to_list(self) -> List[Skill]:
        """Get all skills as a list."""
        return list(self.skills.values())

    def import_from_ai_iq(self, db_path: str) -> int:
        """Import skills from AI-IQ beliefs table.

        Args:
            db_path: Path to AI-IQ memories.db

        Returns:
            Number of skills imported
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

        rows = []
        if 'beliefs' in tables:
            cursor = conn.execute("""
                SELECT statement, confidence, evidence_count, created_at
                FROM beliefs
                WHERE statement LIKE 'skilled at%'
                   OR statement LIKE 'good at%'
                   OR statement LIKE 'expert in%'
                   OR statement LIKE 'proficient in%'
                ORDER BY confidence DESC
            """)
            rows.extend(cursor.fetchall())

        # Also extract skills from memory tags/categories
        if 'memories' in tables and not rows:
            cursor = conn.execute("""
                SELECT DISTINCT tags, category, content FROM memories
                WHERE active = 1 AND category IN ('learning', 'project', 'decision')
                ORDER BY access_count DESC LIMIT 50
            """)
            for row in cursor:
                tags = row['tags'] or ''
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag and len(tag) > 1:
                        skill = Skill(name=tag, confidence=0.7, evidence_count=1)
                        self.add_or_update(skill)
                        imported += 1
            conn.close()
            return imported

        cursor = iter(rows)

        for row in cursor:
            # Extract skill name from statement
            statement = row['statement'].lower()
            skill_name = None

            if 'skilled at' in statement:
                skill_name = statement.split('skilled at')[-1].strip()
            elif 'good at' in statement:
                skill_name = statement.split('good at')[-1].strip()
            elif 'expert in' in statement:
                skill_name = statement.split('expert in')[-1].strip()
            elif 'proficient in' in statement:
                skill_name = statement.split('proficient in')[-1].strip()

            if skill_name:
                skill = Skill(
                    name=skill_name,
                    confidence=row['confidence'] or 0.7,
                    evidence_count=row['evidence_count'] or 0,
                    last_used=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                )
                self.add_or_update(skill)
                imported += 1

        conn.close()
        return imported

    def stats(self) -> Dict[str, Any]:
        """Get statistics about skills."""
        if not self.skills:
            return {
                "total": 0,
                "avg_confidence": 0.0,
                "total_evidence": 0,
            }

        confidences = [s.confidence for s in self.skills.values()]
        evidence = [s.evidence_count for s in self.skills.values()]

        return {
            "total": len(self.skills),
            "avg_confidence": sum(confidences) / len(confidences),
            "total_evidence": sum(evidence),
            "top_skill": max(self.skills.values(), key=lambda s: s.confidence).name,
        }
