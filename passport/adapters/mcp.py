"""MCP (Model Context Protocol) resource adapter.

Reference: https://modelcontextprotocol.io/
"""

from typing import Dict, Any


def export_mcp(card_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Export agent card as MCP-compatible resource.

    Args:
        card_dict: Agent card dictionary

    Returns:
        MCP resource dictionary
    """
    agent_id = card_dict["agent_id"]
    name = card_dict["name"]

    # Build skill summary
    skills = card_dict.get("skills", [])
    skill_names = [s["name"] for s in skills]
    skill_summary = ", ".join(skill_names[:5])
    if len(skills) > 5:
        skill_summary += f" (and {len(skills) - 5} more)"

    # Build description
    description_parts = [f"AI Agent: {name}"]

    if skills:
        description_parts.append(f"Skills: {skill_summary}")

    reputation = card_dict.get("reputation")
    if reputation:
        score = reputation.get("overall_score", 0.5)
        description_parts.append(f"Reputation: {score:.2f}")

    task_history = card_dict.get("task_history")
    if task_history and task_history.get("total_tasks", 0) > 0:
        total = task_history["total_tasks"]
        rate = task_history["success_rate"]
        description_parts.append(f"Tasks: {total} ({rate:.0%} success)")

    description = " | ".join(description_parts)

    # Create MCP resource
    mcp_resource = {
        "uri": f"passport://{agent_id}",
        "name": f"Agent Passport: {name}",
        "description": description,
        "mimeType": "application/json",
        "contents": card_dict,
    }

    # Add annotations for MCP servers
    mcp_resource["annotations"] = {
        "agent_id": agent_id,
        "agent_name": name,
        "skill_count": len(skills),
        "verified": card_dict.get("signature") is not None,
    }

    if reputation:
        mcp_resource["annotations"]["reputation_score"] = reputation["overall_score"]

    return mcp_resource
