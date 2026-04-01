#!/usr/bin/env python3
"""Manual test for MCP server functionality.

This script demonstrates the MCP server in action by:
1. Generating a passport
2. Verifying it
3. Getting skills and reputation
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from passport.mcp_server import (
    passport_generate,
    passport_verify,
    passport_skills,
    passport_reputation,
    get_current_passport,
)
from passport.card import AgentCard
from passport.skills import Skill
from passport.reputation import Reputation


def test_mcp_tools():
    """Test MCP tools directly."""
    print("=== Testing AI-IQ Passport MCP Server ===\n")

    # Test 1: Generate a passport
    print("1. Generating passport...")
    result = passport_generate(name="TestAgent", agent_id="agent-test-123")
    print(f"   Result: {json.dumps(result, indent=2)}\n")

    if not result["success"]:
        print("Failed to generate passport!")
        return

    # Test 2: Get current passport resource
    print("2. Getting current passport resource...")
    passport_data = get_current_passport()
    passport = json.loads(passport_data)
    print(f"   Agent: {passport['name']} ({passport['agent_id']})")
    print(f"   Skills: {len(passport['skills'])}\n")

    # Test 3: Get skills
    print("3. Getting top skills...")
    skills_result = passport_skills(agent_id="current", top_n=5)
    print(f"   Total skills: {skills_result.get('total_skills', 0)}")
    if skills_result.get("top_skills"):
        for skill in skills_result["top_skills"][:3]:
            print(f"   - {skill['name']}: {skill['confidence']:.2f}")
    print()

    # Test 4: Get reputation
    print("4. Getting reputation...")
    rep_result = passport_reputation(agent_id="current")
    if rep_result.get("has_reputation"):
        print(f"   Overall score: {rep_result['overall_score']:.2f}")
    else:
        print(f"   {rep_result.get('message', 'No reputation data')}")
    print()

    # Test 5: Add some skills manually and test again
    print("5. Adding skills to passport...")
    card = AgentCard.load(result["passport_path"])
    card.add_skill(Skill(name="Python", confidence=0.9, evidence_count=50))
    card.add_skill(Skill(name="MCP Protocol", confidence=0.8, evidence_count=25))
    card.add_skill(Skill(name="AI Systems", confidence=0.85, evidence_count=40))
    card.reputation = Reputation(
        overall_score=0.82,
        feedback_score=0.85,
        prediction_accuracy=0.80,
        task_completion_rate=0.85,
        consistency_score=0.75,
        total_feedback=100,
        total_predictions=50,
        total_tasks=75,
    )
    card.save(result["passport_path"])
    print("   Skills added!\n")

    # Test 6: Get updated skills
    print("6. Getting updated top skills...")
    skills_result = passport_skills(agent_id="current", top_n=5)
    print(f"   Total skills: {skills_result.get('total_skills', 0)}")
    for skill in skills_result.get("top_skills", []):
        print(f"   - {skill['name']}: {skill['confidence']:.2f} ({skill['evidence_count']} tasks)")
    print()

    # Test 7: Get updated reputation
    print("7. Getting updated reputation...")
    rep_result = passport_reputation(agent_id="current")
    if rep_result.get("has_reputation"):
        print(f"   Overall score: {rep_result['overall_score']:.2f}")
        print(f"   Breakdown:")
        for key, value in rep_result["breakdown"].items():
            print(f"     - {key}: {value:.2f}")
    print()

    print("=== All tests completed successfully! ===")


if __name__ == "__main__":
    test_mcp_tools()
