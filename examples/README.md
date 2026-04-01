# Examples

This directory contains example scripts demonstrating AI-IQ Passport usage.

## basic_usage.py

Comprehensive example showing all core features:

- Creating an agent passport
- Adding skills with confidence scores
- Adding custom traits
- Saving and loading from JSON
- Exporting to A2A and MCP formats
- Generating signing keys
- Signing and verifying passports

Run it:

```bash
python examples/basic_usage.py
```

The script creates temporary output files and prints their locations.

## peer_exchange_demo.sh

Shell script demonstrating the complete peer exchange workflow:

- Generating passports for two agents
- Starting an HTTP server to expose a passport
- Fetching a remote passport
- Listing known peers
- Marking peers as trusted
- Full exchange handshake

Run it:

```bash
bash examples/peer_exchange_demo.sh
```

This creates a complete demo in `/tmp/passport-demo/` showing how agents can discover each other and build trust networks.

## peer_exchange_api.py

Python example showing how to use peer exchange programmatically:

- Creating agent passports with skills and reputation
- Starting a passport server in a background thread
- Fetching remote passports via HTTP
- Exchanging passports between agents
- Building a local peer registry
- Making automated trust decisions

Run it:

```bash
python examples/peer_exchange_api.py
```

See `PEER_EXCHANGE.md` for complete documentation.

## Using with AI-IQ

If you have an AI-IQ memory system database, you can import skills and reputation directly:

```bash
ai-iq-passport generate \
  --name "MyAgent" \
  --from-ai-iq ~/.ai-iq/memories.db \
  --output agent.json
```

This will:

- Extract skills from `beliefs` table (statements like "skilled at X", "expert in Y")
- Extract tags from frequently accessed memories as skills
- Calculate reputation from `feedback` table (good/bad/meh ratings)
- Calculate prediction accuracy from `predictions` table
- Calculate task completion rate from pending memories

## Integrating with Other Frameworks

See the main README.md for examples of using passports with:

- CrewAI
- A2A Protocol
- MCP (Model Context Protocol)
- Custom agent frameworks
