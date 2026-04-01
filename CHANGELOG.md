# Changelog

All notable changes to AI-IQ Passport will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-01

### Added

- **MCP (Model Context Protocol) Server**: Native integration with Claude Code and other MCP clients
  - `passport://current` resource for reading current agent passport
  - `passport://{agent_id}` resource for reading specific agent passports from registry
  - `passport_generate` tool for creating new passports with optional AI-IQ import
  - `passport_verify` tool for verifying passport signatures
  - `passport_skills` tool for listing top skills with confidence scores
  - `passport_reputation` tool for getting reputation score breakdowns
- MCP server entry point: `ai-iq-passport-mcp` command
- Registry system at `~/.ai-iq-passport/registry/` for multi-agent support
- Optional `mcp` dependency group in pyproject.toml
- Comprehensive MCP documentation in `MCP_README.md`
- Example MCP config file: `mcp_config.json`
- 15 new tests for MCP server functionality (98 tests total)
- Example script: `examples/mcp_test.py`

### Changed

- Updated main README with MCP server usage section
- Updated pyproject.toml with MCP optional dependency and entry point

## [0.1.0] - 2026-03-31

### Added

- Initial release of AI-IQ Passport
- Core `AgentCard` class for portable agent identity
- `Skill` system with confidence scores and evidence tracking
- `Reputation` calculator with weighted scoring from feedback, predictions, tasks, and consistency
- Ed25519 cryptographic signing and verification
- CLI tool with commands: generate, keygen, sign, verify, export, show, skill, refresh
- Export adapters for A2A Agent Card format
- Export adapters for MCP resource format
- Import from AI-IQ memory system (skills from beliefs/tags, reputation from feedback/predictions/tasks)
- Comprehensive test suite with 41 tests
- Documentation and examples

### Supported

- Python 3.8+
- A2A Agent Card format (export)
- MCP resource format (export)
- JSON import/export
- AI-IQ database import

[0.1.0]: https://github.com/kobie3717/ai-iq-passport/releases/tag/v0.1.0
