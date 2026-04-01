"""MCP (Model Context Protocol) server for AI-IQ Passport.

Exposes agent passports as MCP resources and tools for Claude Code integration.

Resources:
  - passport://current - Current agent's passport
  - passport://{agent_id} - Specific agent's passport by ID

Tools:
  - passport_generate - Generate a new passport
  - passport_verify - Verify a passport signature
  - passport_skills - List agent's top skills
  - passport_reputation - Get reputation score breakdown

Usage:
    python -m passport.mcp_server

    Or via MCP config:
    {
        "mcpServers": {
            "ai-iq-passport": {
                "command": "python",
                "args": ["-m", "passport.mcp_server"]
            }
        }
    }
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextContent

from .card import AgentCard
from .signer import generate_keypair, Signer
from .verifier import verify_card
from .skills import SkillManager
from .reputation import ReputationCalculator

# Initialize FastMCP server
mcp = FastMCP(
    name="ai-iq-passport",
    instructions="AI-IQ Passport MCP Server - Exposes agent passports as resources and tools",
)

# Default paths
DEFAULT_PASSPORT_DIR = Path.home() / ".ai-iq-passport"
DEFAULT_PASSPORT_PATH = DEFAULT_PASSPORT_DIR / "passport.json"
DEFAULT_REGISTRY_DIR = DEFAULT_PASSPORT_DIR / "registry"
DEFAULT_AI_IQ_DB = Path.home() / ".ai-iq" / "memories.db"


def get_passport_path(agent_id: Optional[str] = None) -> Path:
    """Get path to a passport file.

    Args:
        agent_id: Agent ID for registry lookup, or None for current agent

    Returns:
        Path to passport file
    """
    if agent_id is None or agent_id == "current":
        return DEFAULT_PASSPORT_PATH

    # Look in registry
    registry_file = DEFAULT_REGISTRY_DIR / f"{agent_id}.json"
    if registry_file.exists():
        return registry_file

    # Fallback to default
    return DEFAULT_PASSPORT_PATH


def ensure_directories() -> None:
    """Ensure default directories exist."""
    DEFAULT_PASSPORT_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)


# Resources


@mcp.resource("passport://current")
def get_current_passport() -> str:
    """Get the current agent's passport."""
    ensure_directories()

    if not DEFAULT_PASSPORT_PATH.exists():
        return json.dumps({
            "error": "No passport found",
            "message": f"No passport at {DEFAULT_PASSPORT_PATH}. Use passport_generate tool to create one.",
        })

    try:
        card = AgentCard.load(str(DEFAULT_PASSPORT_PATH))
        return card.to_json()
    except Exception as e:
        return json.dumps({
            "error": "Failed to load passport",
            "message": str(e),
        })


@mcp.resource("passport://{agent_id}")
def get_passport_by_id(agent_id: str) -> str:
    """Get a specific agent's passport by ID.

    Args:
        agent_id: Agent ID to lookup
    """
    ensure_directories()
    passport_path = get_passport_path(agent_id)

    if not passport_path.exists():
        return json.dumps({
            "error": "Passport not found",
            "message": f"No passport found for agent {agent_id}",
        })

    try:
        card = AgentCard.load(str(passport_path))
        return card.to_json()
    except Exception as e:
        return json.dumps({
            "error": "Failed to load passport",
            "message": str(e),
        })


# Tools


@mcp.tool()
def passport_generate(
    name: str,
    agent_id: Optional[str] = None,
    ai_iq_db: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a new agent passport.

    Args:
        name: Agent name
        agent_id: Optional custom agent ID (auto-generated if not provided)
        ai_iq_db: Optional path to AI-IQ memories.db to import skills/reputation

    Returns:
        Generated passport data with agent_id and file location
    """
    ensure_directories()

    try:
        # Create passport
        card = AgentCard.create(name=name, agent_id=agent_id)

        # Import from AI-IQ if path provided
        if ai_iq_db:
            db_path = Path(ai_iq_db).expanduser()
            if not db_path.exists():
                return {
                    "success": False,
                    "error": f"AI-IQ database not found at {db_path}",
                }

            # Import skills
            skill_manager = SkillManager()
            imported_skills = skill_manager.import_from_ai_iq(str(db_path))
            for skill in skill_manager.to_list():
                card.add_skill(skill)

            # Import reputation
            rep_calc = ReputationCalculator()
            card.reputation = rep_calc.calculate_from_ai_iq(str(db_path))

        # Save passport
        card.save(str(DEFAULT_PASSPORT_PATH))

        # Also save to registry
        registry_file = DEFAULT_REGISTRY_DIR / f"{card.agent_id}.json"
        card.save(str(registry_file))

        return {
            "success": True,
            "agent_id": card.agent_id,
            "name": card.name,
            "passport_path": str(DEFAULT_PASSPORT_PATH),
            "registry_path": str(registry_file),
            "skills_imported": len(card.skills),
            "reputation_score": card.reputation.overall_score if card.reputation else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def passport_verify(passport_json: str, public_key_path: Optional[str] = None) -> Dict[str, Any]:
    """Verify a passport's cryptographic signature.

    Args:
        passport_json: Passport JSON string to verify
        public_key_path: Optional path to public key file (PEM format)

    Returns:
        Verification result with signature status
    """
    try:
        passport_dict = json.loads(passport_json)

        if not passport_dict.get("signature"):
            return {
                "verified": False,
                "error": "Passport has no signature",
            }

        # Default to looking for public key in standard location
        if public_key_path is None:
            keys_dir = DEFAULT_PASSPORT_DIR / "keys"
            public_key_path = str(keys_dir / "agent.pub")

            if not Path(public_key_path).exists():
                return {
                    "verified": False,
                    "error": f"No public key found at {public_key_path}",
                }

        # Verify signature
        is_valid = verify_card(passport_dict, public_key_path=public_key_path)

        return {
            "verified": is_valid,
            "agent_id": passport_dict.get("agent_id"),
            "agent_name": passport_dict.get("name"),
            "signature": passport_dict.get("signature")[:32] + "..." if is_valid else None,
        }

    except json.JSONDecodeError:
        return {
            "verified": False,
            "error": "Invalid JSON",
        }
    except Exception as e:
        return {
            "verified": False,
            "error": str(e),
        }


@mcp.tool()
def passport_skills(agent_id: str = "current", top_n: int = 10) -> Dict[str, Any]:
    """List an agent's top skills with confidence scores.

    Args:
        agent_id: Agent ID or "current" for current agent
        top_n: Number of top skills to return (default: 10)

    Returns:
        List of top skills with confidence scores and evidence counts
    """
    ensure_directories()

    try:
        passport_path = get_passport_path(agent_id)

        if not passport_path.exists():
            return {
                "success": False,
                "error": f"No passport found for agent {agent_id}",
            }

        card = AgentCard.load(str(passport_path))

        # Sort skills by confidence
        sorted_skills = sorted(card.skills, key=lambda s: s.confidence, reverse=True)
        top_skills = sorted_skills[:top_n]

        return {
            "success": True,
            "agent_id": card.agent_id,
            "agent_name": card.name,
            "total_skills": len(card.skills),
            "top_skills": [
                {
                    "name": skill.name,
                    "confidence": skill.confidence,
                    "evidence_count": skill.evidence_count,
                    "tags": skill.tags,
                }
                for skill in top_skills
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
def passport_reputation(agent_id: str = "current") -> Dict[str, Any]:
    """Get an agent's reputation score breakdown.

    Args:
        agent_id: Agent ID or "current" for current agent

    Returns:
        Reputation score breakdown with component scores
    """
    ensure_directories()

    try:
        passport_path = get_passport_path(agent_id)

        if not passport_path.exists():
            return {
                "success": False,
                "error": f"No passport found for agent {agent_id}",
            }

        card = AgentCard.load(str(passport_path))

        if not card.reputation:
            return {
                "success": True,
                "agent_id": card.agent_id,
                "agent_name": card.name,
                "has_reputation": False,
                "message": "No reputation data available",
            }

        rep = card.reputation

        return {
            "success": True,
            "agent_id": card.agent_id,
            "agent_name": card.name,
            "has_reputation": True,
            "overall_score": rep.overall_score,
            "breakdown": {
                "feedback_score": rep.feedback_score,
                "prediction_accuracy": rep.prediction_accuracy,
                "task_completion_rate": rep.task_completion_rate,
                "consistency_score": rep.consistency_score,
            },
            "counts": {
                "total_feedback": rep.total_feedback,
                "total_predictions": rep.total_predictions,
                "total_tasks": rep.total_tasks,
            },
            "last_calculated": rep.last_calculated.isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def main() -> None:
    """Run the MCP server via stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
