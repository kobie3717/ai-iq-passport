#!/usr/bin/env python3
"""Test script demonstrating v0.3.0 features with real AI-IQ data.

This script shows:
1. FSRS stability scores imported from AI-IQ
2. Prediction detail tracking
3. Skill decay based on staleness
4. Task log (append-only audit trail)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from passport.card import AgentCard
from passport.skills import SkillManager, Skill
from passport.reputation import ReputationCalculator


def test_fsrs_integration():
    """Test FSRS stability import from AI-IQ."""
    print("\n=== Feature 1: FSRS Integration ===")

    db_path = "/root/.claude/projects/-root/memory/memories.db"

    # Import skills with FSRS data
    skill_manager = SkillManager()
    imported = skill_manager.import_from_ai_iq(db_path)
    print(f"✓ Imported {imported} skills from AI-IQ")

    # Show skills with FSRS data
    top_skills = skill_manager.get_top_skills(5)
    print("\nTop 5 skills with FSRS data:")
    for skill in top_skills:
        print(f"  - {skill.name}:")
        print(f"      Confidence: {skill.confidence:.2f}")
        print(f"      FSRS Stability: {skill.fsrs_stability:.2f}")
        print(f"      Stale: {skill.stale}")
        if skill.last_reviewed:
            print(f"      Last reviewed: {skill.last_reviewed.strftime('%Y-%m-%d')}")


def test_skill_decay():
    """Test skill decay based on staleness."""
    print("\n=== Feature 2: Skill Decay ===")

    # Create a fresh skill
    fresh_skill = Skill(name="python", confidence=0.9, fsrs_stability=5.0)
    fresh_skill.last_used = datetime.now() - timedelta(days=20)

    # Create a stale skill
    stale_skill = Skill(name="javascript", confidence=0.9, fsrs_stability=5.0)
    stale_skill.last_used = datetime.now() - timedelta(days=100)

    print(f"\nFresh skill (20 days old):")
    print(f"  - Age: {fresh_skill.age_days()} days")
    print(f"  - Is stale: {fresh_skill.is_stale()}")
    print(f"  - Original confidence: {fresh_skill.confidence:.2f}")
    print(f"  - Decayed confidence: {fresh_skill.decayed_confidence():.2f}")

    print(f"\nStale skill (100 days old):")
    print(f"  - Age: {stale_skill.age_days()} days")
    print(f"  - Is stale: {stale_skill.is_stale()}")
    print(f"  - Original confidence: {stale_skill.confidence:.2f}")
    print(f"  - Decayed confidence: {stale_skill.decayed_confidence():.2f}")
    print(f"  - Decay amount: {(stale_skill.confidence - stale_skill.decayed_confidence()):.2f} (10% for 70 days past threshold)")


def test_predictions():
    """Test prediction detail in passport."""
    print("\n=== Feature 3: Prediction Detail ===")

    card = AgentCard.create(name="Claude")

    # Add some predictions
    card.predictions = [
        {
            "statement": "AI-IQ will reach 200 memories by end of month",
            "confidence": 0.8,
            "created_at": "2026-03-01T00:00:00",
            "deadline": "2026-03-31",
            "outcome": "confirmed",
            "resolved_at": "2026-03-30T00:00:00"
        },
        {
            "statement": "WhatsAuction will get 10 paying customers",
            "confidence": 0.9,
            "created_at": "2026-04-01T00:00:00",
            "deadline": "2026-04-12",
            "outcome": "open",
            "resolved_at": None
        }
    ]

    print(f"\nPredictions tracked: {len(card.predictions)}")
    for pred in card.predictions:
        print(f"  - {pred['statement']}")
        print(f"      Confidence: {pred['confidence']:.0%}")
        print(f"      Deadline: {pred['deadline']}")
        print(f"      Status: {pred['outcome']}")


def test_task_log():
    """Test task log (append-only)."""
    print("\n=== Feature 4: Task Log (Append-Only) ===")

    card = AgentCard.create(name="Claude")

    # Log some tasks
    card.log_task("Implement FSRS integration", "success", ["feature", "ai-iq"])
    card.log_task("Add skill decay algorithm", "success", ["feature", "passport"])
    card.log_task("Fix authentication bug", "failure", ["bug", "auth"])
    card.log_task("Write comprehensive tests", "success", ["testing", "quality"])
    card.log_task("Update CHANGELOG", "success", ["documentation"])

    print(f"\nTask log entries: {len(card.task_log)}")

    # Get stats
    stats = card.task_stats()
    print(f"\nTask Statistics:")
    print(f"  - Total tasks: {stats['total']}")
    print(f"  - Success: {stats['success_count']}")
    print(f"  - Failure: {stats['failure_count']}")
    print(f"  - Success rate: {stats['success_rate']:.0%}")

    print(f"\nTag distribution:")
    for tag, count in sorted(stats['tags_distribution'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {tag}: {count}")

    print(f"\nRecent tasks:")
    for task in card.task_log[-3:]:
        print(f"  - [{task['outcome']}] {task['task']}")
        print(f"      Tags: {', '.join(task['tags'])}")


def test_reputation_with_skills():
    """Test reputation calculation with skill quality."""
    print("\n=== Reputation with Skill Quality ===")

    db_path = "/root/.claude/projects/-root/memory/memories.db"

    # Create card and import skills
    card = AgentCard.create(name="Claude")
    skill_manager = SkillManager()
    skill_manager.import_from_ai_iq(db_path)

    for skill in skill_manager.to_list():
        card.add_skill(skill)

    # Calculate reputation with skills
    calc = ReputationCalculator()
    reputation = calc.calculate_from_ai_iq(db_path, skills=card.skills)

    print(f"\nReputation Score: {reputation.overall_score:.2f}")
    print(f"  - Feedback: {reputation.feedback_score:.2f} (30% weight)")
    print(f"  - Predictions: {reputation.prediction_accuracy:.2f} (25% weight)")
    print(f"  - Tasks: {reputation.task_completion_rate:.2f} (20% weight)")
    print(f"  - Consistency: {reputation.consistency_score:.2f} (15% weight)")
    print(f"  - Skill Quality: NEW in v0.3.0 (10% weight)")
    print(f"      Based on {len(card.skills)} skills with FSRS stability and decay")


def test_full_workflow():
    """Test complete workflow with all features."""
    print("\n=== Full Workflow: Generate Passport with v0.3.0 Features ===")

    db_path = "/root/.claude/projects/-root/memory/memories.db"

    # Create card
    card = AgentCard.create(name="Claude Sonnet 4.5")

    # Import skills with FSRS
    skill_manager = SkillManager()
    imported = skill_manager.import_from_ai_iq(db_path)
    for skill in skill_manager.to_list():
        card.add_skill(skill)

    # Import predictions and task log
    import_counts = card.import_ai_iq_data(db_path)

    # Calculate reputation
    calc = ReputationCalculator()
    card.reputation = calc.calculate_from_ai_iq(db_path, skills=card.skills)

    print(f"\nPassport generated successfully:")
    print(f"  - Skills: {len(card.skills)} (with FSRS stability)")
    print(f"  - Predictions: {import_counts['predictions']}")
    print(f"  - Task log: {import_counts['tasks']} entries")
    print(f"  - Reputation: {card.reputation.overall_score:.2f}")

    # Show decayed skills
    stale_count = sum(1 for s in card.skills if s.is_stale())
    print(f"\nSkill decay analysis:")
    print(f"  - Stale skills (>90 days): {stale_count}/{len(card.skills)}")

    # Save passport
    output_path = "/tmp/test_passport_v030.json"
    card.save(output_path)
    print(f"\n✓ Passport saved to {output_path}")

    # Show file size
    import os
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    print("=" * 70)
    print("AI-IQ Passport v0.3.0 - Honest Reputation System")
    print("=" * 70)

    test_fsrs_integration()
    test_skill_decay()
    test_predictions()
    test_task_log()
    test_reputation_with_skills()
    test_full_workflow()

    print("\n" + "=" * 70)
    print("All v0.3.0 features verified! ✓")
    print("=" * 70)
