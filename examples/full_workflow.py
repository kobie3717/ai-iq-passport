#!/usr/bin/env python3
"""Full workflow demonstration of AI-IQ Passport MCP integration.

This script shows a complete end-to-end workflow:
1. Generate a passport
2. Add skills programmatically
3. Add reputation data
4. Access via MCP resources
5. Query via MCP tools
6. Show the killer feature: seamless Claude Code integration
"""

import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from passport.card import AgentCard, Skill
from passport.reputation import Reputation
from passport.mcp_server import (
    passport_generate,
    passport_skills,
    passport_reputation,
    get_current_passport,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def main():
    """Run the full workflow demonstration."""
    print("\n🎯 AI-IQ Passport MCP Integration - Full Workflow Demo\n")

    # Step 1: Generate base passport
    print_section("1. Generate Base Passport")
    result = passport_generate(name="ClaudeCodeAssistant", agent_id="agent-demo-001")
    print(f"✓ Generated passport: {result['agent_id']}")
    print(f"✓ Location: {result['passport_path']}")

    # Step 2: Load and enhance with skills
    print_section("2. Add Skills Programmatically")
    card = AgentCard.load(result['passport_path'])

    skills_to_add = [
        Skill(name="Python Development", confidence=0.95, evidence_count=150, tags=["programming", "backend"]),
        Skill(name="API Design", confidence=0.90, evidence_count=100, tags=["architecture", "rest"]),
        Skill(name="MCP Protocol", confidence=0.88, evidence_count=75, tags=["protocols", "integration"]),
        Skill(name="Agent Frameworks", confidence=0.85, evidence_count=60, tags=["ai", "frameworks"]),
        Skill(name="Database Design", confidence=0.82, evidence_count=80, tags=["data", "architecture"]),
        Skill(name="Testing & QA", confidence=0.80, evidence_count=120, tags=["quality", "testing"]),
        Skill(name="Documentation", confidence=0.78, evidence_count=90, tags=["writing", "docs"]),
        Skill(name="Code Review", confidence=0.75, evidence_count=110, tags=["quality", "collaboration"]),
    ]

    for skill in skills_to_add:
        card.add_skill(skill)
        print(f"  + {skill.name}: {skill.confidence:.2f} ({skill.evidence_count} tasks)")

    # Step 3: Add reputation data
    print_section("3. Add Reputation Data")
    card.reputation = Reputation(
        overall_score=0.87,
        feedback_score=0.90,
        prediction_accuracy=0.85,
        task_completion_rate=0.88,
        consistency_score=0.82,
        total_feedback=250,
        total_predictions=80,
        total_tasks=320,
    )
    print(f"✓ Overall reputation: {card.reputation.overall_score:.2f}")
    print(f"  - Feedback score: {card.reputation.feedback_score:.2f}")
    print(f"  - Prediction accuracy: {card.reputation.prediction_accuracy:.2f}")
    print(f"  - Task completion: {card.reputation.task_completion_rate:.2f}")
    print(f"  - Consistency: {card.reputation.consistency_score:.2f}")

    # Save enhanced passport
    card.save(result['passport_path'])
    print(f"\n✓ Saved enhanced passport")

    # Step 4: Access via MCP resource
    print_section("4. Access via MCP Resource (passport://current)")
    passport_data = get_current_passport()
    passport_obj = json.loads(passport_data)
    print(f"✓ Agent: {passport_obj['name']}")
    print(f"✓ ID: {passport_obj['agent_id']}")
    print(f"✓ Skills: {len(passport_obj['skills'])}")
    print(f"✓ Has reputation: {passport_obj['reputation'] is not None}")

    # Step 5: Query top skills via MCP tool
    print_section("5. Query Top Skills via MCP Tool")
    skills_result = passport_skills(agent_id="current", top_n=5)
    print(f"✓ Total skills: {skills_result['total_skills']}")
    print(f"\nTop 5 skills:")
    for i, skill in enumerate(skills_result['top_skills'], 1):
        tags_str = ", ".join(skill['tags'][:2]) if skill['tags'] else "no tags"
        print(f"  {i}. {skill['name']}")
        print(f"     Confidence: {skill['confidence']:.2f} | Evidence: {skill['evidence_count']} tasks")
        print(f"     Tags: {tags_str}")

    # Step 6: Get reputation via MCP tool
    print_section("6. Get Reputation via MCP Tool")
    rep_result = passport_reputation(agent_id="current")
    print(f"✓ Agent: {rep_result['agent_name']}")
    print(f"✓ Overall score: {rep_result['overall_score']:.2f}")
    print(f"\nBreakdown:")
    for key, value in rep_result['breakdown'].items():
        print(f"  - {key.replace('_', ' ').title()}: {value:.2f}")
    print(f"\nActivity counts:")
    for key, value in rep_result['counts'].items():
        print(f"  - {key.replace('_', ' ').title()}: {value}")

    # Step 7: Show the killer feature
    print_section("7. The Killer Feature: Claude Code Integration")
    print("""
With this MCP server, you can now do this in Claude Code:

┌─────────────────────────────────────────────────────────┐
│ User: Show me my agent passport                         │
│                                                          │
│ Claude: *reads passport://current*                      │
│ You are ClaudeCodeAssistant (agent-demo-001).           │
│ You have 8 skills with an overall reputation of 0.87.   │
│                                                          │
│ User: What are my top 3 skills?                         │
│                                                          │
│ Claude: *uses passport_skills tool*                     │
│ Your top 3 skills are:                                  │
│ 1. Python Development (0.95 confidence, 150 tasks)      │
│ 2. API Design (0.90 confidence, 100 tasks)              │
│ 3. MCP Protocol (0.88 confidence, 75 tasks)             │
│                                                          │
│ User: How's my reputation?                              │
│                                                          │
│ Claude: *uses passport_reputation tool*                 │
│ Your overall reputation is 0.87/1.0. Breakdown:         │
│ - Feedback: 0.90 (250 ratings)                          │
│ - Prediction accuracy: 0.85 (80 predictions)            │
│ - Task completion: 0.88 (320 tasks)                     │
│ - Consistency: 0.82                                     │
└─────────────────────────────────────────────────────────┘

No manual JSON reading. No CLI commands. Just natural language
interaction with your agent's portable identity and reputation.

That's the power of MCP integration. 🚀
""")

    # Summary
    print_section("Summary")
    print("""
✓ Passport generated and enhanced
✓ MCP resources working (passport://current)
✓ MCP tools working (passport_skills, passport_reputation)
✓ Ready for Claude Code integration

Next steps:
1. Add this to your Claude Code MCP config:
   {
     "mcpServers": {
       "ai-iq-passport": {
         "command": "python",
         "args": ["-m", "passport.mcp_server"]
       }
     }
   }

2. Restart Claude Code

3. Try: "Read passport://current" or "Show me my top skills"

See MCP_README.md for complete documentation.
""")


if __name__ == "__main__":
    main()
