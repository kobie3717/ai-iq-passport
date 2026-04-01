"""Command-line interface for AI-IQ Passport."""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Optional

from . import __version__
from .card import AgentCard, TaskSummary
from .skills import Skill, SkillManager
from .reputation import ReputationCalculator
from .signer import Signer, generate_keypair
from .verifier import verify_card
from .adapters import export_json, import_json, export_a2a, export_mcp


def cmd_generate(args):
    """Generate a new passport."""
    # Create basic card
    card = AgentCard.create(name=args.name, agent_id=args.agent_id)

    # Import from AI-IQ if requested
    if args.from_ai_iq:
        db_path = args.from_ai_iq
        if not os.path.exists(db_path):
            print(f"Error: AI-IQ database not found at {db_path}", file=sys.stderr)
            return 1

        print(f"Importing from AI-IQ database: {db_path}")

        # Import skills
        skill_manager = SkillManager()
        imported_skills = skill_manager.import_from_ai_iq(db_path)
        print(f"  - Imported {imported_skills} skills")

        for skill in skill_manager.to_list():
            card.add_skill(skill)

        # Import predictions and task logs
        import_counts = card.import_ai_iq_data(db_path)
        print(f"  - Imported {import_counts['predictions']} predictions")
        print(f"  - Imported {import_counts['tasks']} task log entries")

        # Calculate reputation (pass skills for quality scoring)
        reputation_calc = ReputationCalculator()
        reputation = reputation_calc.calculate_from_ai_iq(db_path, skills=card.skills)
        card.reputation = reputation
        print(f"  - Calculated reputation: {reputation.overall_score:.2f}")

        # Update task history from reputation data
        card.task_history.total_tasks = reputation.total_tasks
        card.task_history.completed_tasks = int(
            reputation.total_tasks * reputation.task_completion_rate
        )
        card.task_history.failed_tasks = (
            reputation.total_tasks - card.task_history.completed_tasks
        )
        card.task_history.success_rate = reputation.task_completion_rate

        if reputation.total_feedback > 0:
            card.task_history.avg_feedback_score = reputation.feedback_score

    # Add traits
    if args.traits:
        for trait in args.traits:
            if "=" in trait:
                key, value = trait.split("=", 1)
                card.add_trait(key, value)

    # Save
    output = args.output or "passport.json"
    card.save(output)
    print(f"\nPassport generated: {output}")
    print(f"\nSummary:\n{card.summary()}")

    return 0


def cmd_keygen(args):
    """Generate signing keys."""
    output_dir = args.output_dir
    private_key_path, public_key_path = generate_keypair(output_dir)

    print(f"Keys generated successfully:")
    print(f"  Private key: {private_key_path}")
    print(f"  Public key: {public_key_path}")
    print(f"\nIMPORTANT: Keep your private key secure!")

    return 0


def cmd_sign(args):
    """Sign a passport."""
    # Load card
    try:
        card = AgentCard.load(args.passport)
    except Exception as e:
        print(f"Error loading passport: {e}", file=sys.stderr)
        return 1

    # Load private key
    try:
        signer = Signer.from_file(args.key)
    except Exception as e:
        print(f"Error loading private key: {e}", file=sys.stderr)
        return 1

    # Sign
    card_dict = card.to_dict()
    signature = signer.sign_card(card_dict)
    card.signature = signature

    # Save
    output = args.output or args.passport
    card.save(output)

    print(f"Passport signed: {output}")
    print(f"Signature: {signature[:64]}...")

    return 0


def cmd_verify(args):
    """Verify a passport signature."""
    # Load card
    try:
        card = AgentCard.load(args.passport)
    except Exception as e:
        print(f"Error loading passport: {e}", file=sys.stderr)
        return 1

    if not card.signature:
        print("Error: Passport is not signed", file=sys.stderr)
        return 1

    # Verify
    try:
        is_valid = verify_card(card.to_dict(), public_key_path=args.pubkey)

        if is_valid:
            print(f"✓ Signature valid for {card.name} ({card.agent_id})")
            return 0
        else:
            print(f"✗ Signature invalid for {card.name} ({card.agent_id})", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error verifying signature: {e}", file=sys.stderr)
        return 1


def cmd_export(args):
    """Export passport to different format."""
    # Load card
    try:
        card = AgentCard.load(args.passport)
    except Exception as e:
        print(f"Error loading passport: {e}", file=sys.stderr)
        return 1

    card_dict = card.to_dict()

    # Export based on format
    if args.format == "a2a":
        exported = export_a2a(card_dict)
    elif args.format == "mcp":
        exported = export_mcp(card_dict)
    else:  # json
        exported = card_dict

    # Output
    output_json = json.dumps(exported, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"Exported to {args.output} ({args.format} format)")
    else:
        print(output_json)

    return 0


def cmd_show(args):
    """Show passport summary."""
    # Load card
    try:
        card = AgentCard.load(args.passport)
    except Exception as e:
        print(f"Error loading passport: {e}", file=sys.stderr)
        return 1

    # Show summary
    print(card.summary())

    # Show full JSON if requested
    if args.full:
        print("\n" + "=" * 60)
        print("Full JSON:")
        print("=" * 60)
        print(card.to_json())

    return 0


def cmd_skill_add(args):
    """Add a skill to a passport."""
    # Load card
    try:
        card = AgentCard.load(args.passport)
    except Exception as e:
        print(f"Error loading passport: {e}", file=sys.stderr)
        return 1

    # Create skill
    skill = Skill(
        name=args.skill_name,
        confidence=args.confidence,
        evidence_count=args.evidence,
        tags=args.tags.split(",") if args.tags else [],
    )

    # Add to card
    card.add_skill(skill)

    # Save
    card.save(args.passport)
    print(f"Added skill '{args.skill_name}' with confidence {args.confidence:.2f}")

    return 0


def cmd_refresh(args):
    """Refresh passport from AI-IQ."""
    # Load card
    try:
        card = AgentCard.load(args.passport)
    except Exception as e:
        print(f"Error loading passport: {e}", file=sys.stderr)
        return 1

    # Check AI-IQ database
    if not args.from_ai_iq:
        print("Error: --from-ai-iq required", file=sys.stderr)
        return 1

    db_path = args.from_ai_iq
    if not os.path.exists(db_path):
        print(f"Error: AI-IQ database not found at {db_path}", file=sys.stderr)
        return 1

    print(f"Refreshing from AI-IQ database: {db_path}")

    # Re-import skills
    skill_manager = SkillManager()
    imported_skills = skill_manager.import_from_ai_iq(db_path)
    print(f"  - Imported {imported_skills} skills")

    # Update card skills
    card.skills = skill_manager.to_list()

    # Recalculate reputation
    reputation_calc = ReputationCalculator()
    reputation = reputation_calc.calculate_from_ai_iq(db_path)
    card.reputation = reputation
    print(f"  - Updated reputation: {reputation.overall_score:.2f}")

    # Update task history
    card.task_history.total_tasks = reputation.total_tasks
    card.task_history.completed_tasks = int(
        reputation.total_tasks * reputation.task_completion_rate
    )
    card.task_history.failed_tasks = (
        reputation.total_tasks - card.task_history.completed_tasks
    )
    card.task_history.success_rate = reputation.task_completion_rate

    # Save
    card.save(args.passport)
    print(f"\nPassport refreshed: {args.passport}")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ai-iq-passport",
        description="Portable AI agent identity & reputation layer",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a new passport")
    gen_parser.add_argument("--name", required=True, help="Agent name")
    gen_parser.add_argument("--agent-id", help="Agent ID (generated if not provided)")
    gen_parser.add_argument(
        "--from-ai-iq", metavar="DB_PATH", help="Import from AI-IQ memories.db"
    )
    gen_parser.add_argument("--output", "-o", help="Output file (default: passport.json)")
    gen_parser.add_argument(
        "--traits", nargs="*", help="Traits as key=value pairs"
    )

    # Keygen command
    keygen_parser = subparsers.add_parser("keygen", help="Generate signing keys")
    keygen_parser.add_argument(
        "--output-dir", help="Output directory (default: ~/.ai-iq-passport/keys/)"
    )

    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign a passport")
    sign_parser.add_argument("passport", help="Passport JSON file")
    sign_parser.add_argument("--key", required=True, help="Private key file")
    sign_parser.add_argument("--output", "-o", help="Output file (default: overwrite)")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a passport signature")
    verify_parser.add_argument("passport", help="Passport JSON file")
    verify_parser.add_argument("--pubkey", required=True, help="Public key file")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export to different format")
    export_parser.add_argument("passport", help="Passport JSON file")
    export_parser.add_argument(
        "--format",
        choices=["a2a", "mcp", "json"],
        default="json",
        help="Export format",
    )
    export_parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show passport summary")
    show_parser.add_argument("passport", help="Passport JSON file")
    show_parser.add_argument("--full", action="store_true", help="Show full JSON")

    # Skill add command
    skill_parser = subparsers.add_parser("skill", help="Add a skill")
    skill_parser.add_argument("action", choices=["add"], help="Action")
    skill_parser.add_argument("skill_name", help="Skill name")
    skill_parser.add_argument("--passport", default="passport.json", help="Passport file")
    skill_parser.add_argument(
        "--confidence", type=float, default=0.7, help="Confidence (0.0-1.0)"
    )
    skill_parser.add_argument(
        "--evidence", type=int, default=0, help="Evidence count"
    )
    skill_parser.add_argument("--tags", help="Comma-separated tags")

    # Refresh command
    refresh_parser = subparsers.add_parser("refresh", help="Refresh from AI-IQ")
    refresh_parser.add_argument("--passport", default="passport.json", help="Passport file")
    refresh_parser.add_argument(
        "--from-ai-iq", required=True, metavar="DB_PATH", help="AI-IQ memories.db path"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handlers
    commands = {
        "generate": cmd_generate,
        "keygen": cmd_keygen,
        "sign": cmd_sign,
        "verify": cmd_verify,
        "export": cmd_export,
        "show": cmd_show,
        "skill": cmd_skill_add,
        "refresh": cmd_refresh,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
