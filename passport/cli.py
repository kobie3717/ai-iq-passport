"""Command-line interface for AI-IQ Passport."""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
import urllib.request
import urllib.error

from . import __version__
from .card import AgentCard, TaskSummary
from .skills import Skill, SkillManager
from .reputation import ReputationCalculator
from .signer import Signer, generate_keypair
from .verifier import verify_card
from .adapters import export_json, import_json, export_a2a, export_mcp
from .server import serve_passport


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


def cmd_serve(args):
    """Serve passport over HTTP."""
    return serve_passport(
        passport_path=args.passport,
        port=args.port,
        host=args.host,
    )


def cmd_fetch(args):
    """Fetch and display a remote passport."""
    url = args.url
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    if not url.endswith("/passport"):
        url = f"{url}/passport"

    try:
        print(f"Fetching passport from {url}...")
        with urllib.request.urlopen(url, timeout=10) as response:
            passport_data = json.loads(response.read().decode("utf-8"))

        # Display passport info
        agent_id = passport_data.get("agent_id", "unknown")
        name = passport_data.get("name", "unknown")
        signature = passport_data.get("signature")

        print(f"\nAgent: {name}")
        print(f"ID: {agent_id}")
        print(f"Version: {passport_data.get('version', 'unknown')}")
        print(f"Created: {passport_data.get('created_at', 'unknown')}")
        print(f"Updated: {passport_data.get('updated_at', 'unknown')}")
        print(f"Signed: {'Yes' if signature else 'No'}")

        # Show reputation
        reputation = passport_data.get("reputation")
        if reputation:
            print(f"\nReputation:")
            print(f"  Overall Score: {reputation.get('overall_score', 0):.2f}")
            print(f"  Total Tasks: {reputation.get('total_tasks', 0)}")
            print(f"  Completion Rate: {reputation.get('task_completion_rate', 0):.1%}")

        # Show top skills
        skills = passport_data.get("skills", [])
        if skills:
            print(f"\nTop Skills:")
            sorted_skills = sorted(skills, key=lambda s: s.get("confidence", 0), reverse=True)
            for skill in sorted_skills[:5]:
                conf = skill.get("confidence", 0)
                skill_name = skill.get("name", "unknown")
                evidence = skill.get("evidence_count", 0)
                print(f"  - {skill_name} (confidence: {conf:.2f}, evidence: {evidence})")

        # Show task summary
        task_history = passport_data.get("task_history")
        if task_history:
            print(f"\nTask History:")
            print(f"  Total: {task_history.get('total_tasks', 0)}")
            print(f"  Completed: {task_history.get('completed_tasks', 0)}")
            print(f"  Failed: {task_history.get('failed_tasks', 0)}")
            print(f"  Success Rate: {task_history.get('success_rate', 0):.1%}")

        # Check staleness
        updated_at = passport_data.get("updated_at")
        if updated_at:
            try:
                updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                age_days = (datetime.now().astimezone() - updated_dt).days
                if age_days > 30:
                    print(f"\nWARNING: Passport is {age_days} days old (stale)")
            except:
                pass

        # Save if requested
        if args.save:
            peers_dir = Path.home() / ".ai-iq-passport" / "peers"
            peers_dir.mkdir(parents=True, exist_ok=True)

            # Use agent_id as filename
            filename = f"{agent_id}.json"
            filepath = peers_dir / filename

            with open(filepath, "w") as f:
                json.dump(passport_data, f, indent=2)

            print(f"\nSaved to: {filepath}")

        return 0

    except urllib.error.URLError as e:
        print(f"Error fetching passport: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error parsing passport: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_trust(args):
    """Mark an agent as trusted."""
    peers_file = Path.home() / ".ai-iq-passport" / "peers.json"

    # Load existing peers registry
    if peers_file.exists():
        with open(peers_file, "r") as f:
            peers = json.load(f)
    else:
        peers = {}

    # Check if agent exists in peers directory
    peers_dir = Path.home() / ".ai-iq-passport" / "peers"
    agent_file = peers_dir / f"{args.agent_id}.json"

    if not agent_file.exists():
        print(f"Error: Agent {args.agent_id} not found in peers directory", file=sys.stderr)
        print(f"Use 'fetch --save' to save the agent's passport first", file=sys.stderr)
        return 1

    # Mark as trusted
    if args.agent_id not in peers:
        peers[args.agent_id] = {}

    peers[args.agent_id]["trusted"] = True
    peers[args.agent_id]["trusted_at"] = datetime.now().isoformat()

    # Save peers registry
    peers_file.parent.mkdir(parents=True, exist_ok=True)
    with open(peers_file, "w") as f:
        json.dump(peers, f, indent=2)

    print(f"Marked {args.agent_id} as trusted")
    return 0


def cmd_peers(args):
    """List all known peers."""
    peers_dir = Path.home() / ".ai-iq-passport" / "peers"
    peers_file = Path.home() / ".ai-iq-passport" / "peers.json"

    if not peers_dir.exists() or not any(peers_dir.iterdir()):
        print("No peers found. Use 'fetch --save' to add peers.")
        return 0

    # Load trust registry
    trust_registry = {}
    if peers_file.exists():
        with open(peers_file, "r") as f:
            trust_registry = json.load(f)

    # List all peer files
    peer_files = list(peers_dir.glob("*.json"))

    if not peer_files:
        print("No peers found.")
        return 0

    print(f"\nKnown Peers ({len(peer_files)}):")
    print("=" * 80)

    for peer_file in sorted(peer_files):
        try:
            with open(peer_file, "r") as f:
                passport_data = json.load(f)

            agent_id = passport_data.get("agent_id", "unknown")
            name = passport_data.get("name", "unknown")

            # Check trust status
            trust_info = trust_registry.get(agent_id, {})
            trusted = trust_info.get("trusted", False)
            trust_mark = "[TRUSTED]" if trusted else "[untrusted]"

            # Get reputation
            reputation = passport_data.get("reputation", {})
            overall_score = reputation.get("overall_score", 0)

            # Get top skills
            skills = passport_data.get("skills", [])
            top_skills = sorted(skills, key=lambda s: s.get("confidence", 0), reverse=True)[:3]
            skill_names = [s.get("name", "unknown") for s in top_skills]

            print(f"\n{trust_mark} {name} ({agent_id[:16]}...)")
            print(f"  Reputation: {overall_score:.2f}")
            print(f"  Top Skills: {', '.join(skill_names) if skill_names else 'None'}")
            print(f"  File: {peer_file}")

        except Exception as e:
            print(f"\nError reading {peer_file}: {e}")

    print()
    return 0


def cmd_exchange(args):
    """Exchange passports with a remote agent."""
    url = args.url
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    if not url.endswith("/exchange"):
        url = f"{url}/exchange"

    # Load our passport
    passport_path = args.passport or str(Path.home() / ".ai-iq-passport" / "passport.json")

    try:
        with open(passport_path, "r") as f:
            our_passport = json.load(f)
    except Exception as e:
        print(f"Error loading our passport: {e}", file=sys.stderr)
        return 1

    # Send our passport, receive theirs
    try:
        print(f"Exchanging passports with {url}...")

        data = json.dumps(our_passport).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            their_passport = json.loads(response.read().decode("utf-8"))

        # Display their passport
        agent_id = their_passport.get("agent_id", "unknown")
        name = their_passport.get("name", "unknown")

        print(f"\nExchange successful!")
        print(f"Remote Agent: {name}")
        print(f"Remote ID: {agent_id}")

        # Show reputation
        reputation = their_passport.get("reputation")
        if reputation:
            print(f"Reputation: {reputation.get('overall_score', 0):.2f}")

        # Show top skills
        skills = their_passport.get("skills", [])
        if skills:
            sorted_skills = sorted(skills, key=lambda s: s.get("confidence", 0), reverse=True)
            skill_names = [s.get("name", "unknown") for s in sorted_skills[:5]]
            print(f"Top Skills: {', '.join(skill_names)}")

        # Save peer
        peers_dir = Path.home() / ".ai-iq-passport" / "peers"
        peers_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{agent_id}.json"
        filepath = peers_dir / filename

        with open(filepath, "w") as f:
            json.dump(their_passport, f, indent=2)

        print(f"\nSaved peer to: {filepath}")
        print(f"\nUse 'ai-iq-passport trust {agent_id}' to mark as trusted")

        return 0

    except urllib.error.URLError as e:
        print(f"Error exchanging passports: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


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

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Serve passport over HTTP")
    serve_parser.add_argument(
        "--passport",
        help="Passport file (default: ~/.ai-iq-passport/passport.json)",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8500, help="Port to listen on (default: 8500)"
    )
    serve_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )

    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch a remote passport")
    fetch_parser.add_argument("url", help="URL of remote passport server (host:port)")
    fetch_parser.add_argument(
        "--save", action="store_true", help="Save to local peers directory"
    )

    # Trust command
    trust_parser = subparsers.add_parser("trust", help="Mark an agent as trusted")
    trust_parser.add_argument("agent_id", help="Agent ID to trust")

    # Peers command
    peers_parser = subparsers.add_parser("peers", help="List all known peers")

    # Exchange command
    exchange_parser = subparsers.add_parser("exchange", help="Exchange passports with a remote agent")
    exchange_parser.add_argument("url", help="URL of remote passport server (host:port)")
    exchange_parser.add_argument(
        "--passport",
        help="Our passport file (default: ~/.ai-iq-passport/passport.json)",
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
        "serve": cmd_serve,
        "fetch": cmd_fetch,
        "trust": cmd_trust,
        "peers": cmd_peers,
        "exchange": cmd_exchange,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
