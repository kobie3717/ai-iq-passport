#!/usr/bin/env python3
"""Demo script showcasing tamper-resistance features.

This demonstrates:
1. FSRS stability + difficulty in skills
2. Prediction detail tracking
3. Passport age checking
4. Task log audit trail
"""

from datetime import datetime, timedelta
from passport import AgentCard, Skill, Prediction, TaskEntry
from passport.predictions import PredictionManager
from passport.task_log import TaskLog


def demo_feature_1_fsrs_stability():
    """Feature 1: FSRS stability + difficulty."""
    print("\n=== Feature 1: FSRS Stability + Difficulty ===\n")

    # Suspicious skill: high confidence, low stability
    suspicious = Skill(
        name="expert-skill",
        confidence=0.95,
        evidence_count=100,
        fsrs_stability=0.8,  # LOW - not tested over time
        fsrs_difficulty=7.0
    )

    # Legitimate skill: high confidence, high stability
    legitimate = Skill(
        name="python",
        confidence=0.92,
        evidence_count=100,
        fsrs_stability=8.5,  # HIGH - proven over time
        fsrs_difficulty=6.5
    )

    print("Suspicious Pattern (gaming?):")
    print(f"  Confidence: {suspicious.confidence}")
    print(f"  Stability:  {suspicious.fsrs_stability} ← RED FLAG")
    print(f"  Difficulty: {suspicious.fsrs_difficulty}")

    print("\nLegitimate Pattern:")
    print(f"  Confidence: {legitimate.confidence}")
    print(f"  Stability:  {legitimate.fsrs_stability} ← Tested over time")
    print(f"  Difficulty: {legitimate.fsrs_difficulty}")


def demo_feature_2_prediction_detail():
    """Feature 2: Prediction detail (not just counts)."""
    print("\n=== Feature 2: Prediction Detail ===\n")

    manager = PredictionManager()

    # Add predictions with full detail
    manager.add(Prediction(
        statement="Python will dominate AI development in 2026",
        confidence=0.85,
        created_at="2026-01-01T00:00:00",
        deadline="2026-12-31T23:59:59",
        outcome="confirmed",
        resolved_at="2026-06-15T10:00:00",
        expected_outcome="Python market share > 60%",
        actual_outcome="Python market share = 67% (GitHub ML repos)"
    ))

    manager.add(Prediction(
        statement="Rust will overtake Go for backend services",
        confidence=0.65,
        created_at="2026-01-15T00:00:00",
        deadline="2026-12-31T23:59:59",
        outcome="refuted",
        resolved_at="2026-09-01T14:00:00",
        expected_outcome="Rust adoption > Go adoption",
        actual_outcome="Go still leads 58% vs Rust 42%"
    ))

    stats = manager.get_stats()

    print("Prediction Track Record:")
    print(f"  Total:    {stats['total']}")
    print(f"  Confirmed: {stats['confirmed']}")
    print(f"  Refuted:   {stats['refuted']}")
    print(f"  Accuracy:  {stats['accuracy']:.1%}")

    print("\nDetailed Predictions:")
    for pred in manager.predictions:
        print(f"\n  Statement: {pred.statement}")
        print(f"  Confidence: {pred.confidence}")
        print(f"  Outcome: {pred.outcome}")
        print(f"  Expected: {pred.expected_outcome}")
        print(f"  Actual: {pred.actual_outcome}")


def demo_feature_3_passport_age():
    """Feature 3: Passport age tracking and freshness."""
    print("\n=== Feature 3: Passport Age Tracking ===\n")

    card = AgentCard.create(name="DemoAgent")

    # Add fresh skill
    fresh_skill = Skill(name="python", confidence=0.9)
    card.add_skill(fresh_skill)

    # Add stale skill
    stale_skill = Skill(name="cobol", confidence=0.6)
    stale_skill.last_used = datetime.now() - timedelta(days=120)
    card.add_skill(stale_skill)

    # Check age
    stale_skills, metadata = card.age_check(stale_threshold_days=30)

    print("Passport Freshness:")
    print(f"  Age: {metadata['passport_age_days']} days")
    print(f"  Total skills: {metadata['total_skills']}")
    print(f"  Stale skills: {metadata['stale_skills_count']}")
    print(f"  Freshness score: {metadata['freshness_score']:.2f}")
    print(f"  Needs refresh: {metadata['needs_refresh']}")

    print("\nStale Skills:")
    for skill in stale_skills:
        print(f"  - {skill.name}: last used {skill.age_days()} days ago")
        print(f"    Confidence: {skill.confidence:.2f} → Decayed: {skill.decayed_confidence():.2f}")


def demo_feature_4_task_log():
    """Feature 4: Task log (append-only audit trail)."""
    print("\n=== Feature 4: Task Log (Audit Trail) ===\n")

    log = TaskLog()

    # Add tasks
    log.add(TaskEntry(
        task_id="task-001",
        description="Implement ML model for sentiment analysis",
        completed_at="2026-03-15T10:00:00",
        skill_used="python",
        outcome="success",
        feedback="good"
    ))

    log.add(TaskEntry(
        task_id="task-002",
        description="Optimize database queries",
        completed_at="2026-03-16T14:00:00",
        skill_used="sql",
        outcome="success",
        feedback="good"
    ))

    log.add(TaskEntry(
        task_id="task-003",
        description="Fix authentication bug in production",
        completed_at="2026-03-17T09:00:00",
        skill_used="debugging",
        outcome="failure",
        feedback="bad"
    ))

    log.add(TaskEntry(
        task_id="task-004",
        description="Refactor legacy codebase",
        completed_at="2026-03-18T11:00:00",
        skill_used="python",
        outcome="partial",
        feedback="meh"
    ))

    stats = log.get_stats()

    print("Task Log Summary:")
    print(f"  Total tasks: {stats['total']}")
    print(f"  Success: {stats['success']}")
    print(f"  Failure: {stats['failure']}")
    print(f"  Partial: {stats['partial']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")

    print("\nSkill Usage Distribution:")
    for skill, count in stats['skill_usage'].items():
        print(f"  {skill}: {count} tasks")

    print("\nRecent Tasks:")
    for task in log.entries[:5]:
        print(f"  [{task.outcome}] {task.description}")
        print(f"      Skill: {task.skill_used}, Feedback: {task.feedback}")


def demo_integration():
    """Full integration: all features together."""
    print("\n=== Full Integration: All Features ===\n")

    card = AgentCard.create(name="ProductionAgent")

    # Add skill with FSRS data
    skill = Skill(
        name="distributed-systems",
        confidence=0.88,
        evidence_count=75,
        fsrs_stability=6.8,
        fsrs_difficulty=8.5
    )
    card.add_skill(skill)

    # Add predictions
    card.predictions = [
        {
            "statement": "Microservices will trend toward smaller teams",
            "confidence": 0.75,
            "created_at": "2026-01-01",
            "deadline": "2026-12-31",
            "outcome": "confirmed"
        }
    ]

    # Add task log
    card.task_log = [
        {
            "task_id": "t1",
            "description": "Design distributed cache system",
            "completed_at": "2026-03-20",
            "skill_used": "distributed-systems",
            "outcome": "success",
            "feedback": "good"
        }
    ]

    # Get passport metadata
    card_dict = card.to_dict()

    print("Passport Export:")
    print(f"  Agent: {card_dict['name']}")
    print(f"  Skills: {len(card_dict['skills'])}")
    print(f"    - {card_dict['skills'][0]['name']}")
    print(f"      Confidence: {card_dict['skills'][0]['confidence']}")
    print(f"      FSRS Stability: {card_dict['skills'][0]['fsrs_stability']}")
    print(f"      FSRS Difficulty: {card_dict['skills'][0]['fsrs_difficulty']}")
    print(f"  Predictions: {len(card_dict['predictions'])}")
    print(f"  Task Log: {len(card_dict['task_log'])}")
    print(f"  Passport Age: {card_dict['passport_age_days']} days")
    print(f"  Freshness Score: {card_dict['freshness_score']:.2f}")

    print("\n✓ All tamper-resistance features integrated!")


if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   AI-IQ Passport: Tamper-Resistance Features Demo    ║")
    print("╚═══════════════════════════════════════════════════════╝")

    demo_feature_1_fsrs_stability()
    demo_feature_2_prediction_detail()
    demo_feature_3_passport_age()
    demo_feature_4_task_log()
    demo_integration()

    print("\n" + "="*60)
    print("Demo complete! See TAMPER_RESISTANCE_UPGRADE.md for details.")
    print("="*60)
