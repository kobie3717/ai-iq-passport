#!/usr/bin/env python3
"""Example: Using peer exchange programmatically."""

import json
import threading
import time
import urllib.request
from pathlib import Path

from passport.card import AgentCard
from passport.skills import Skill
from passport.reputation import Reputation
from passport.server import serve_passport, PassportRequestHandler
from http.server import HTTPServer


def create_sample_agent(name, agent_id):
    """Create a sample agent passport."""
    card = AgentCard.create(name=name, agent_id=agent_id)

    if "Python" in name:
        card.add_skill(Skill(name="Python", confidence=0.95, evidence_count=50))
        card.add_skill(Skill(name="Testing", confidence=0.85, evidence_count=30))
        card.add_skill(Skill(name="API Design", confidence=0.80, evidence_count=20))
    else:
        card.add_skill(Skill(name="JavaScript", confidence=0.92, evidence_count=45))
        card.add_skill(Skill(name="React", confidence=0.88, evidence_count=35))
        card.add_skill(Skill(name="WebDev", confidence=0.85, evidence_count=40))

    card.reputation = Reputation(
        overall_score=0.87,
        total_tasks=100,
        task_completion_rate=0.92,
    )

    return card


def start_passport_server(passport_path, port):
    """Start a passport server in a background thread."""

    def run_server():
        with open(passport_path, "r") as f:
            passport_data = json.load(f)

        PassportRequestHandler.passport_data = passport_data
        PassportRequestHandler.passport_path = passport_path

        server = HTTPServer(("127.0.0.1", port), PassportRequestHandler)
        print(f"Server running on port {port}")

        # Run for a limited time
        for _ in range(100):
            server.handle_request()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(0.5)  # Give server time to start
    return thread


def fetch_passport(url):
    """Fetch a passport from a remote server."""
    if not url.endswith("/passport"):
        url = f"{url}/passport"

    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_passports(url, our_passport_path):
    """Exchange passports with a remote server."""
    if not url.endswith("/exchange"):
        url = f"{url}/exchange"

    # Load our passport
    with open(our_passport_path, "r") as f:
        our_passport = json.load(f)

    # Send our passport, receive theirs
    data = json.dumps(our_passport).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    """Demonstrate peer exchange workflow."""
    print("=== AI-IQ Passport Peer Exchange API Demo ===\n")

    # Create temporary directory for demo
    demo_dir = Path("/tmp/passport-api-demo")
    demo_dir.mkdir(exist_ok=True)

    # 1. Create two agent passports
    print("1. Creating agent passports...")
    agent_a = create_sample_agent("PythonAgent", "python-expert-001")
    agent_b = create_sample_agent("JSAgent", "javascript-expert-002")

    # Save passports
    passport_a_path = demo_dir / "agent_a.json"
    passport_b_path = demo_dir / "agent_b.json"

    agent_a.save(str(passport_a_path))
    agent_b.save(str(passport_b_path))

    print(f"  - Created: {agent_a.name} ({agent_a.agent_id})")
    print(f"  - Created: {agent_b.name} ({agent_b.agent_id})")
    print()

    # 2. Start server for Agent A
    print("2. Starting server for Agent A...")
    port = 8520
    server_thread = start_passport_server(str(passport_a_path), port)
    print()

    # 3. Fetch Agent A's passport
    print("3. Fetching Agent A's passport...")
    try:
        remote_passport = fetch_passport(f"http://localhost:{port}")
        print(f"  - Agent: {remote_passport['name']}")
        print(f"  - ID: {remote_passport['agent_id']}")
        print(
            f"  - Reputation: {remote_passport.get('reputation', {}).get('overall_score', 0):.2f}"
        )
        print(
            f"  - Skills: {len(remote_passport.get('skills', []))} ({', '.join([s['name'] for s in remote_passport.get('skills', [])])})"
        )
        print()
    except Exception as e:
        print(f"  Error fetching passport: {e}")
        return

    # 4. Exchange passports
    print("4. Exchanging passports...")
    try:
        their_passport = exchange_passports(
            f"http://localhost:{port}", str(passport_b_path)
        )
        print(f"  - Received from: {their_passport['name']}")
        print(f"  - Their ID: {their_passport['agent_id']}")
        print(
            f"  - Their reputation: {their_passport.get('reputation', {}).get('overall_score', 0):.2f}"
        )
        print()
    except Exception as e:
        print(f"  Error exchanging passports: {e}")
        return

    # 5. Save peer to local registry
    print("5. Saving peer to local registry...")
    peers_dir = demo_dir / "peers"
    peers_dir.mkdir(exist_ok=True)

    peer_file = peers_dir / f"{their_passport['agent_id']}.json"
    with open(peer_file, "w") as f:
        json.dump(their_passport, f, indent=2)

    print(f"  - Saved to: {peer_file}")
    print()

    # 6. Trust decision
    print("6. Trust decision...")
    reputation_score = their_passport.get("reputation", {}).get("overall_score", 0)
    skill_count = len(their_passport.get("skills", []))

    if reputation_score > 0.8 and skill_count >= 3:
        print(f"  - TRUSTED: High reputation ({reputation_score:.2f}) and {skill_count} skills")
        trust_status = "trusted"
    else:
        print(f"  - UNTRUSTED: Reputation ({reputation_score:.2f}) or skills ({skill_count}) below threshold")
        trust_status = "untrusted"

    # Save trust registry
    trust_registry_file = demo_dir / "peers.json"
    trust_registry = {}
    if trust_registry_file.exists():
        with open(trust_registry_file, "r") as f:
            trust_registry = json.load(f)

    trust_registry[their_passport["agent_id"]] = {
        "trusted": trust_status == "trusted",
        "reputation_at_trust": reputation_score,
        "skill_count": skill_count,
    }

    with open(trust_registry_file, "w") as f:
        json.dump(trust_registry, f, indent=2)

    print()
    print("=== Demo Complete ===")
    print(f"\nFiles created:")
    print(f"  - Agent A: {passport_a_path}")
    print(f"  - Agent B: {passport_b_path}")
    print(f"  - Peers: {peers_dir}")
    print(f"  - Trust registry: {trust_registry_file}")


if __name__ == "__main__":
    main()
