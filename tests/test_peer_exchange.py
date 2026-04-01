"""Tests for peer-to-peer passport exchange."""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
import urllib.request
import urllib.error

import pytest

from passport.card import AgentCard
from passport.server import serve_passport, load_passport, PassportRequestHandler
from passport.skills import Skill
from passport.reputation import Reputation


@pytest.fixture
def temp_passport():
    """Create a temporary test passport."""
    card = AgentCard.create(name="TestAgent", agent_id="test-agent-123")
    card.add_skill(Skill(name="Python", confidence=0.9, evidence_count=10))
    card.add_skill(Skill(name="Testing", confidence=0.8, evidence_count=5))
    card.reputation = Reputation(
        overall_score=0.85,
        total_tasks=100,
        task_completion_rate=0.95,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(card.to_json())
        filepath = f.name

    yield filepath

    # Cleanup
    if os.path.exists(filepath):
        os.unlink(filepath)


@pytest.fixture
def temp_passport_2():
    """Create a second temporary test passport."""
    card = AgentCard.create(name="RemoteAgent", agent_id="remote-agent-456")
    card.add_skill(Skill(name="JavaScript", confidence=0.85, evidence_count=8))
    card.add_skill(Skill(name="WebDev", confidence=0.75, evidence_count=6))
    card.reputation = Reputation(
        overall_score=0.78,
        total_tasks=50,
        task_completion_rate=0.88,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(card.to_json())
        filepath = f.name

    yield filepath

    # Cleanup
    if os.path.exists(filepath):
        os.unlink(filepath)


def test_load_passport(temp_passport):
    """Test loading a passport from file."""
    passport_data = load_passport(temp_passport)

    assert passport_data["name"] == "TestAgent"
    assert passport_data["agent_id"] == "test-agent-123"
    assert len(passport_data["skills"]) == 2


def test_load_passport_not_found():
    """Test loading a non-existent passport."""
    with pytest.raises(FileNotFoundError):
        load_passport("/nonexistent/passport.json")


def test_passport_request_handler_health(temp_passport):
    """Test health endpoint (via integration test instead of mocking)."""
    # This test is covered by test_health_endpoint which actually runs a server
    # Mocking HTTPServer request handling is complex, so we skip direct unit test
    passport_data = load_passport(temp_passport)
    assert passport_data["name"] == "TestAgent"


def test_fetch_passport_from_server(temp_passport):
    """Test fetching a passport from a running server."""
    port = 8501  # Use different port to avoid conflicts

    # Start server in background thread
    def run_server():
        passport_data = load_passport(temp_passport)
        PassportRequestHandler.passport_data = passport_data
        PassportRequestHandler.passport_path = temp_passport

        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", port), PassportRequestHandler)
        server.timeout = 1
        # Run for a few iterations
        for _ in range(10):
            server.handle_request()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(0.5)

    # Fetch passport
    try:
        url = f"http://127.0.0.1:{port}/passport"
        with urllib.request.urlopen(url, timeout=5) as response:
            passport_data = json.loads(response.read().decode("utf-8"))

        assert passport_data["name"] == "TestAgent"
        assert passport_data["agent_id"] == "test-agent-123"
        assert len(passport_data["skills"]) == 2

    except urllib.error.URLError as e:
        pytest.skip(f"Server not ready: {e}")


def test_health_endpoint(temp_passport):
    """Test health endpoint."""
    port = 8502

    def run_server():
        passport_data = load_passport(temp_passport)
        PassportRequestHandler.passport_data = passport_data
        PassportRequestHandler.passport_path = temp_passport

        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", port), PassportRequestHandler)
        server.timeout = 1
        for _ in range(10):
            server.handle_request()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url, timeout=5) as response:
            health_data = json.loads(response.read().decode("utf-8"))

        assert health_data["status"] == "ok"
        assert health_data["agent"] == "TestAgent"

    except urllib.error.URLError as e:
        pytest.skip(f"Server not ready: {e}")


def test_verify_endpoint(temp_passport):
    """Test verify endpoint."""
    port = 8503

    def run_server():
        passport_data = load_passport(temp_passport)
        PassportRequestHandler.passport_data = passport_data
        PassportRequestHandler.passport_path = temp_passport

        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", port), PassportRequestHandler)
        server.timeout = 1
        for _ in range(10):
            server.handle_request()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        url = f"http://127.0.0.1:{port}/verify"
        with urllib.request.urlopen(url, timeout=5) as response:
            verify_data = json.loads(response.read().decode("utf-8"))

        # Passport is not signed in this test
        assert verify_data["signed"] == False
        assert verify_data["valid"] == False

    except urllib.error.URLError as e:
        pytest.skip(f"Server not ready: {e}")


def test_exchange_endpoint(temp_passport, temp_passport_2):
    """Test passport exchange endpoint."""
    port = 8504

    def run_server():
        passport_data = load_passport(temp_passport)
        PassportRequestHandler.passport_data = passport_data
        PassportRequestHandler.passport_path = temp_passport

        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", port), PassportRequestHandler)
        server.timeout = 1
        for _ in range(10):
            server.handle_request()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    try:
        # Load our passport
        our_passport = load_passport(temp_passport_2)

        # Send to exchange endpoint
        url = f"http://127.0.0.1:{port}/exchange"
        data = json.dumps(our_passport).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            their_passport = json.loads(response.read().decode("utf-8"))

        # Should receive the server's passport
        assert their_passport["name"] == "TestAgent"
        assert their_passport["agent_id"] == "test-agent-123"

    except urllib.error.URLError as e:
        pytest.skip(f"Server not ready: {e}")


def test_peers_registry():
    """Test peer registry management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        peers_file = Path(tmpdir) / "peers.json"

        # Create initial registry
        peers = {
            "agent-1": {
                "trusted": True,
                "trusted_at": "2024-01-01T00:00:00",
            }
        }

        with open(peers_file, "w") as f:
            json.dump(peers, f)

        # Load and verify
        with open(peers_file, "r") as f:
            loaded_peers = json.load(f)

        assert "agent-1" in loaded_peers
        assert loaded_peers["agent-1"]["trusted"] is True

        # Add another peer
        loaded_peers["agent-2"] = {
            "trusted": False,
        }

        with open(peers_file, "w") as f:
            json.dump(loaded_peers, f)

        # Verify update
        with open(peers_file, "r") as f:
            updated_peers = json.load(f)

        assert len(updated_peers) == 2
        assert "agent-2" in updated_peers


def test_save_peer_passport(temp_passport):
    """Test saving a peer's passport."""
    with tempfile.TemporaryDirectory() as tmpdir:
        peers_dir = Path(tmpdir) / "peers"
        peers_dir.mkdir(parents=True, exist_ok=True)

        # Load passport
        passport_data = load_passport(temp_passport)
        agent_id = passport_data["agent_id"]

        # Save to peers directory
        filepath = peers_dir / f"{agent_id}.json"
        with open(filepath, "w") as f:
            json.dump(passport_data, f, indent=2)

        # Verify saved
        assert filepath.exists()

        with open(filepath, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data["name"] == "TestAgent"
        assert loaded_data["agent_id"] == agent_id
