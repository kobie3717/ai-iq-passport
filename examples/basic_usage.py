#!/usr/bin/env python3
"""Basic usage example for AI-IQ Passport.

This script demonstrates:
1. Creating a new agent passport
2. Adding skills with confidence scores
3. Adding traits
4. Saving to JSON
5. Loading from JSON
6. Exporting to A2A and MCP formats
7. Signing and verifying a passport
"""

import os
import tempfile
from pathlib import Path

from passport import AgentCard, Skill, generate_keypair, verify_card
from passport.adapters import export_a2a, export_mcp


def main():
    # Create temporary directory for output
    output_dir = Path(tempfile.mkdtemp(prefix="passport-example-"))
    print(f"Output directory: {output_dir}\n")

    # 1. Create a new agent passport
    print("=" * 60)
    print("Step 1: Creating agent passport")
    print("=" * 60)

    card = AgentCard.create(
        name="ExampleAgent",
        agent_id="agent-example-001"
    )
    print(f"Created passport for: {card.name} ({card.agent_id})\n")

    # 2. Add skills with confidence scores
    print("=" * 60)
    print("Step 2: Adding skills")
    print("=" * 60)

    skills = [
        Skill(
            name="Python development",
            confidence=0.9,
            evidence_count=50,
            tags=["programming", "backend", "python"]
        ),
        Skill(
            name="API design",
            confidence=0.85,
            evidence_count=35,
            tags=["architecture", "rest", "api"]
        ),
        Skill(
            name="Database optimization",
            confidence=0.75,
            evidence_count=20,
            tags=["database", "performance", "sql"]
        ),
    ]

    for skill in skills:
        card.add_skill(skill)
        print(f"  Added: {skill.name} (confidence: {skill.confidence:.2f})")

    print()

    # 3. Add custom traits
    print("=" * 60)
    print("Step 3: Adding traits")
    print("=" * 60)

    card.add_trait("framework", "CrewAI")
    card.add_trait("model", "claude-sonnet-4.5")
    card.add_trait("specialization", "backend services")

    for key, value in card.traits.items():
        print(f"  {key}: {value}")

    print()

    # 4. Save to JSON
    print("=" * 60)
    print("Step 4: Saving to JSON")
    print("=" * 60)

    passport_path = output_dir / "agent_passport.json"
    card.save(str(passport_path))
    print(f"Saved to: {passport_path}\n")

    # 5. Load from JSON
    print("=" * 60)
    print("Step 5: Loading from JSON")
    print("=" * 60)

    loaded_card = AgentCard.load(str(passport_path))
    print("Loaded passport summary:")
    print("-" * 60)
    print(loaded_card.summary())
    print()

    # 6. Export to different formats
    print("=" * 60)
    print("Step 6: Exporting to A2A and MCP formats")
    print("=" * 60)

    # Export to A2A
    a2a_card = export_a2a(card.to_dict())
    a2a_path = output_dir / "agent_a2a.json"
    import json
    with open(a2a_path, "w") as f:
        json.dump(a2a_card, f, indent=2)
    print(f"A2A format saved to: {a2a_path}")

    # Export to MCP
    mcp_resource = export_mcp(card.to_dict())
    mcp_path = output_dir / "agent_mcp.json"
    with open(mcp_path, "w") as f:
        json.dump(mcp_resource, f, indent=2)
    print(f"MCP format saved to: {mcp_path}\n")

    # 7. Sign and verify the passport
    print("=" * 60)
    print("Step 7: Signing and verifying")
    print("=" * 60)

    # Generate keypair
    keys_dir = output_dir / "keys"
    private_key_path, public_key_path = generate_keypair(str(keys_dir))
    print(f"Generated keypair:")
    print(f"  Private key: {private_key_path}")
    print(f"  Public key: {public_key_path}")

    # Sign the passport
    from passport import Signer
    signer = Signer.from_file(private_key_path)
    card_dict = card.to_dict()
    signature = signer.sign_card(card_dict)
    card.signature = signature
    print(f"Signed passport: {signature[:32]}...")

    # Save signed passport
    signed_path = output_dir / "agent_passport_signed.json"
    card.save(str(signed_path))
    print(f"Saved signed passport to: {signed_path}")

    # Verify signature
    is_valid = verify_card(card.to_dict(), public_key_path=public_key_path)
    print(f"Signature verification: {'VALID' if is_valid else 'INVALID'}")

    print()
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)
    print(f"\nAll files saved to: {output_dir}")
    print("\nCreated files:")
    for file in sorted(output_dir.rglob("*")):
        if file.is_file():
            print(f"  {file.relative_to(output_dir)}")


if __name__ == "__main__":
    main()
