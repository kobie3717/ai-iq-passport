# Changelog

All notable changes to AI-IQ Passport will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
