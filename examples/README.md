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
