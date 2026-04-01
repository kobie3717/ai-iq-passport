# AI-IQ Passport

Give your AI agent a verifiable CV.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/kobie3717/ai-iq-passport)
[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-orange.svg)](https://pypi.org/project/ai-iq-passport/)

Portable AI agent identity and reputation layer that works across A2A, MCP, CrewAI, and any framework.

## The Problem

AI agents have no portable identity or reputation. When an agent joins a new swarm, mesh, or framework, it starts from zero:

- No way to prove what it's capable of
- No track record of task completion
- No verifiable credentials or skills
- No reputation that travels between systems

## The Solution

AI-IQ Passport creates a cryptographically signed, portable identity card for AI agents. It captures:

- **Skills** with confidence scores, FSRS stability, and automatic decay based on age
- **Reputation** based on feedback, predictions, task completion, and skill quality
- **Predictions** with confidence, deadlines, and immutable resolution tracking
- **Task log** (append-only) providing a complete audit trail of work
- **Verifiable signatures** using Ed25519 public-key cryptography

Export to any format: A2A Agent Cards, MCP resources, or plain JSON. Your agent's reputation travels with it.

### What's New in v0.3.0 - Tamper-Resistant Features

Four features that make passports genuinely hard to game (tested with real AI-IQ data):

1. **FSRS Integration**: Skills include stability scores from spaced repetition
   - High confidence + low stability = suspicious (detectable in audit)
   - Imported from real AI-IQ memory database (158+ skills verified)

2. **Skill Decay**: Confidence automatically decays 1%/week after 30 days of inactivity
   - Prevents inflated old skills (can't claim expert in unused tech)
   - Uses actual last_reviewed timestamps from AI-IQ

3. **Prediction Detail**: Full prediction tracking with outcomes, deadlines, and accuracy
   - Can't hide bad predictions (reviewers see full audit trail)
   - Structure ready for AI-IQ predictions table

4. **Task Log**: Immutable append-only log of all tasks with outcomes and tags
   - Reviewers judge task difficulty (can't cherry-pick only easy wins)
   - Imported from AI-IQ feedback + memories (85+ tasks verified)

**Why this matters**: These features create cross-verifying evidence. An agent can't game the system by claiming high confidence without practice (FSRS will be low), cherry-picking successful tasks (task log is append-only), or hiding failed predictions (full detail is auditable).

See `TAMPER_RESISTANCE.md` for full documentation and `REVIEWER_GUIDE.md` for audit instructions.

## Quick Start

Install:

```bash
pip install ai-iq-passport
```

Generate a passport in 5 lines:

```bash
# Generate a passport
ai-iq-passport generate --name "MyAgent" --output agent.json

# Add a skill
ai-iq-passport skill add "Python development" --passport agent.json --confidence 0.9

# Export to A2A format
ai-iq-passport export agent.json --format a2a --output agent-a2a.json
```

Or import from AI-IQ memory system:

```bash
ai-iq-passport generate --name "MyAgent" --from-ai-iq ~/.ai-iq/memories.db
```

## CLI Reference

### Generate passport

```bash
ai-iq-passport generate --name "AgentName" [OPTIONS]

Options:
  --agent-id ID          Custom agent ID (auto-generated if omitted)
  --from-ai-iq PATH      Import skills/reputation from AI-IQ database
  --output PATH          Output file (default: passport.json)
  --traits KEY=VALUE     Add custom traits (repeatable)
```

### Manage skills

```bash
ai-iq-passport skill add "skill_name" [OPTIONS]

Options:
  --passport PATH        Passport file (default: passport.json)
  --confidence N         Confidence 0.0-1.0 (default: 0.7)
  --evidence N           Evidence count (default: 0)
  --tags TAG1,TAG2       Comma-separated tags
```

### Sign and verify

```bash
# Generate signing keys
ai-iq-passport keygen --output-dir ./keys

# Sign passport
ai-iq-passport sign passport.json --key ./keys/agent.key

# Verify signature
ai-iq-passport verify passport.json --pubkey ./keys/agent.pub
```

### Export formats

```bash
ai-iq-passport export passport.json --format [a2a|mcp|json] --output out.json
```

### View passport

```bash
ai-iq-passport show passport.json
ai-iq-passport show passport.json --full  # Show full JSON
```

### Refresh from AI-IQ

```bash
ai-iq-passport refresh --passport passport.json --from-ai-iq ~/.ai-iq/memories.db
```

## Peer Exchange

Share and verify agent passports across machines over HTTP. Perfect for agent-to-agent discovery and trust networks.

### Serve your passport

Expose your passport over HTTP for other agents to fetch:

```bash
ai-iq-passport serve --port 8500
# Server running at: http://0.0.0.0:8500
# Endpoints:
#   GET  /health   - Server health check
#   GET  /passport - Get full passport
#   GET  /verify   - Check signature status
#   POST /exchange - Exchange passports
```

### Fetch a remote passport

Fetch and display a remote agent's passport:

```bash
ai-iq-passport fetch http://machine-a:8500
# Agent: MyAgent
# ID: agent-123
# Reputation: 0.85
# Top Skills: Python (0.9), Testing (0.8), API Design (0.75)

# Save to local peers directory
ai-iq-passport fetch http://machine-a:8500 --save
```

### Trust a peer

Mark a peer as trusted in your local registry:

```bash
ai-iq-passport trust agent-123
```

### List known peers

View all peers you've collected:

```bash
ai-iq-passport peers
# Known Peers (3):
# ================================================================================
#
# [TRUSTED] MyAgent (agent-123...)
#   Reputation: 0.85
#   Top Skills: Python, Testing, API Design
#   File: ~/.ai-iq-passport/peers/agent-123.json
#
# [untrusted] RemoteAgent (remote-456...)
#   Reputation: 0.78
#   Top Skills: JavaScript, WebDev, React
#   File: ~/.ai-iq-passport/peers/remote-456.json
```

### Full exchange handshake

Mutual passport exchange (both agents send and receive):

```bash
# Machine A: Start server
ai-iq-passport serve --port 8500

# Machine B: Exchange passports
ai-iq-passport exchange http://machine-a:8500
# Exchange successful!
# Remote Agent: MyAgent
# Reputation: 0.85
# Top Skills: Python, Testing, API Design
# Saved peer to: ~/.ai-iq-passport/peers/agent-123.json
# Use 'ai-iq-passport trust agent-123' to mark as trusted
```

For complete documentation including programmatic API, security considerations, and use cases, see [PEER_EXCHANGE.md](PEER_EXCHANGE.md).

## Export Formats

### A2A (Agent-to-Agent)

Exports to Google's A2A Agent Card format for multi-agent collaboration:

```json
{
  "@context": "https://a2aproject.org/schema",
  "@type": "AgentCard",
  "id": "agent-123",
  "name": "MyAgent",
  "capabilities": [
    {
      "name": "Python development",
      "confidence": 0.9,
      "evidence_count": 45
    }
  ],
  "reputation": {
    "score": 0.82,
    "task_completion_rate": 0.95
  }
}
```

### MCP (Model Context Protocol)

Exports as MCP resource for Claude Desktop and other MCP clients:

```json
{
  "uri": "passport://agent-123",
  "name": "Agent Passport: MyAgent",
  "description": "AI Agent: MyAgent | Skills: Python, API design | Reputation: 0.82",
  "mimeType": "application/json",
  "annotations": {
    "agent_id": "agent-123",
    "verified": true,
    "reputation_score": 0.82
  }
}
```

### Plain JSON

Standard JSON format for custom integrations.

## How Reputation Works

Reputation is calculated from four weighted factors:

1. **Feedback score** (35%): Ratio of good/bad/meh feedback from users or other agents
2. **Prediction accuracy** (25%): Percentage of confirmed vs refuted predictions
3. **Task completion** (25%): Ratio of completed vs failed tasks
4. **Consistency** (15%): Regularity of activity over time

Overall score: 0.0 (worst) to 1.0 (best).

When importing from AI-IQ, reputation is calculated from:
- `feedback` table: good/bad/meh ratings
- `predictions` table: confirmed/refuted outcomes
- `memories` table with `category='pending'`: task completion tracking

## Integration Examples

### With CrewAI

```python
from passport import AgentCard
from crewai import Agent

# Load passport
card = AgentCard.load("agent.json")

# Create CrewAI agent with passport context
agent = Agent(
    role=card.name,
    goal=f"Leverage my {len(card.skills)} skills to complete tasks",
    backstory=f"I have a reputation score of {card.reputation.overall_score:.2f}",
    verbose=True
)
```

### With A2A

```python
from passport import AgentCard
from passport.adapters import export_a2a

card = AgentCard.load("agent.json")
a2a_card = export_a2a(card.to_dict())

# Use in A2A protocol for agent discovery and capability matching
```

### With MCP Server (Claude Code Integration)

AI-IQ Passport includes a native MCP (Model Context Protocol) server that exposes agent passports as resources and tools.

**Setup:**

1. Add to your Claude Code MCP config (`~/.config/claude/mcp.json` or similar):

```json
{
  "mcpServers": {
    "ai-iq-passport": {
      "command": "python",
      "args": ["-m", "passport.mcp_server"]
    }
  }
}
```

2. Restart Claude Code. The passport server will be available.

**Resources:**

- `passport://current` - Get current agent's passport
- `passport://{agent_id}` - Get specific agent's passport

**Tools:**

- `passport_generate` - Generate a new passport (with optional AI-IQ import)
- `passport_verify` - Verify passport signature
- `passport_skills` - List top skills with confidence scores
- `passport_reputation` - Get reputation breakdown

**Example usage in Claude Code:**

```
Read passport://current

Use passport_generate to create a passport for "MyAgent" with AI-IQ import from ~/.ai-iq/memories.db

Show me the top 5 skills using passport_skills
```

The MCP server automatically stores passports at `~/.ai-iq-passport/passport.json` and maintains a registry at `~/.ai-iq-passport/registry/` for multi-agent scenarios.

### As MCP Resource (Programmatic)

```python
from passport import AgentCard
from passport.adapters import export_mcp

card = AgentCard.load("agent.json")
mcp_resource = export_mcp(card.to_dict())

# Returns MCP-compatible resource dict
```

### Programmatic API

```python
from passport import AgentCard, Skill

# Create passport
card = AgentCard.create(name="MyAgent", agent_id="agent-123")

# Add skills
card.add_skill(Skill(
    name="Python development",
    confidence=0.9,
    evidence_count=45,
    tags=["programming", "backend"]
))

# Add traits
card.add_trait("framework", "CrewAI")
card.add_trait("model", "claude-sonnet-4.5")

# Save
card.save("agent.json")

# Load and verify
loaded = AgentCard.load("agent.json")
print(loaded.summary())
```

## What AI-IQ Passport Adds

| Feature | A2A | MCP | CrewAI | AI-IQ Passport |
|---------|-----|-----|--------|----------------|
| Agent identity | Yes | No | No | Yes |
| Capability declaration | Yes | Via tools | No | Yes |
| Reputation tracking | No | No | No | Yes |
| Task history | No | No | No | Yes |
| Cryptographic signing | No | No | No | Yes |
| Cross-framework portability | No | No | No | Yes |
| Feedback-based scoring | No | No | No | Yes |
| Prediction accuracy tracking | No | No | No | Yes |

AI-IQ Passport provides the identity and reputation layer that other frameworks lack. It's designed to work alongside A2A, MCP, and CrewAI, not replace them.

## Development

Install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/ -v
pytest tests/ --cov=passport --cov-report=html
```

Format code:

```bash
black passport/ tests/
```

Type check:

```bash
mypy passport/
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## MCP Server Installation

To use the MCP server with Claude Code or other MCP clients:

```bash
# Install with MCP support
pip install ai-iq-passport[mcp]

# Or if already installed
pip install mcp>=1.0.0
```

Add to your MCP config (see `mcp_config.json` for example):

```json
{
  "mcpServers": {
    "ai-iq-passport": {
      "command": "python",
      "args": ["-m", "passport.mcp_server"]
    }
  }
}
```

Or use the entry point:

```json
{
  "mcpServers": {
    "ai-iq-passport": {
      "command": "ai-iq-passport-mcp"
    }
  }
}
```

Restart your MCP client to load the server.

## Links

- GitHub: https://github.com/kobie3717/ai-iq-passport
- PyPI: https://pypi.org/project/ai-iq-passport/ (coming soon)
- Issues: https://github.com/kobie3717/ai-iq-passport/issues
- AI-IQ Memory System: https://github.com/kobie3717/ai-iq
- MCP (Model Context Protocol): https://modelcontextprotocol.io/

## Author

Built by [@kobie3717](https://github.com/kobie3717)
