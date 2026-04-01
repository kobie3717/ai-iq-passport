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
    fsrs_stability: float = 0.0
    fsrs_difficulty: float = 5.0
    last_reviewed: Optional[datetime] = None
    stale: bool = False

    def __post_init__(self):
        """Validate confidence range."""
        self.confidence = max(0.0, min(1.0, self.confidence))

    def age_days(self) -> int:
        """Days since this skill was last used/reviewed."""
        ref = self.last_reviewed or self.last_used
        return (datetime.now() - ref).days

    def is_stale(self, threshold_days: int = 90) -> bool:
        """Whether this skill should be considered stale."""
        return self.age_days() > threshold_days

    def decayed_confidence(self) -> float:
        """Confidence adjusted for staleness. Decays 1% per week after 30 days of no use."""
        age = self.age_days()
        if age <= 30:
            return self.confidence
        weeks_stale = (age - 30) / 7
        decay = min(weeks_stale * 0.01, 0.5)  # Max 50% decay
        return max(self.confidence - decay, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "last_used": self.last_used.isoformat(),
            "tags": self.tags,
            "fsrs_stability": self.fsrs_stability,
            "fsrs_difficulty": self.fsrs_difficulty,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "stale": self.stale,
            "decayed_confidence": self.decayed_confidence(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create from dictionary."""
        last_used = datetime.fromisoformat(data["last_used"])
        last_reviewed = None
        if data.get("last_reviewed"):
            last_reviewed = datetime.fromisoformat(data["last_reviewed"])

        return cls(
            name=data["name"],
            confidence=data.get("confidence", 0.5),
            evidence_count=data.get("evidence_count", 0),
            last_used=last_used,
            tags=data.get("tags", []),
            fsrs_stability=data.get("fsrs_stability", 0.0),
            fsrs_difficulty=data.get("fsrs_difficulty", 5.0),
            last_reviewed=last_reviewed,
            stale=data.get("stale", False),
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
        """Import skills from AI-IQ memories table with FSRS data.

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

        # Extract skills from memory tags/categories with FSRS data
        if 'memories' in tables:
            # Get aggregated FSRS data per tag
            cursor = conn.execute("""
                SELECT
                    tags,
                    AVG(fsrs_stability) as avg_stability,
                    AVG(fsrs_difficulty) as avg_difficulty,
                    MAX(accessed_at) as last_accessed,
                    MAX(stale) as is_stale,
                    COUNT(*) as evidence_count,
                    AVG(access_count) as avg_access
                FROM memories
                WHERE active = 1
                  AND tags IS NOT NULL
                  AND tags != ''
                  AND category IN ('learning', 'project', 'decision', 'architecture')
                GROUP BY tags
                ORDER BY avg_access DESC, evidence_count DESC
                LIMIT 100
            """)

            tag_stats = {}
            for row in cursor:
                tags = row['tags'] or ''
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag and len(tag) > 1:
                        if tag not in tag_stats:
                            tag_stats[tag] = {
                                'fsrs_stability': row['avg_stability'] or 1.0,
                                'fsrs_difficulty': row['avg_difficulty'] or 5.0,
                                'last_accessed': row['last_accessed'],
                                'stale': bool(row['is_stale']),
                                'evidence_count': row['evidence_count'] or 1,
                                'avg_access': row['avg_access'] or 0
                            }

            # Create skills from tag stats
            for tag_name, stats in tag_stats.items():
                # Calculate confidence from access patterns
                confidence = min(0.9, 0.5 + (stats['avg_access'] * 0.05))

                last_reviewed = None
                if stats['last_accessed']:
                    try:
                        last_reviewed = datetime.fromisoformat(stats['last_accessed'])
                    except (ValueError, TypeError):
                        pass

                skill = Skill(
                    name=tag_name,
                    confidence=confidence,
                    evidence_count=stats['evidence_count'],
                    last_used=last_reviewed or datetime.now(),
                    fsrs_stability=stats['fsrs_stability'],
                    fsrs_difficulty=stats['fsrs_difficulty'],
                    last_reviewed=last_reviewed,
                    stale=stats['stale'],
                    tags=[tag_name]
                )
                self.add_or_update(skill)
                imported += 1

        # Also process beliefs if they exist
        for row in rows:
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

            if skill_name and skill_name not in self.skills:
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
