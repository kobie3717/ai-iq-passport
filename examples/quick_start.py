#!/usr/bin/env python3
"""Quick start example - minimal code to create and use a passport."""

from passport import AgentCard, Skill

# Create passport
card = AgentCard.create(name="QuickAgent")

# Add skills
card.add_skill(Skill(name="Python", confidence=0.9, evidence_count=50))
card.add_skill(Skill(name="API design", confidence=0.85, evidence_count=30))

# Add traits
card.add_trait("framework", "CrewAI")
card.add_trait("model", "claude-sonnet-4.5")

# Save
card.save("quick_passport.json")

# Load and display
loaded = AgentCard.load("quick_passport.json")
print(loaded.summary())
