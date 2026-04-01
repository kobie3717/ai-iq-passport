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

    # Add predictions and task log counts
    predictions = card_dict.get("predictions", [])
    if predictions:
        mcp_resource["annotations"]["prediction_count"] = len(predictions)
        confirmed = sum(1 for p in predictions if p.get("outcome") == "confirmed")
        if confirmed > 0:
            mcp_resource["annotations"]["prediction_accuracy"] = confirmed / len(predictions)

    task_log = card_dict.get("task_log", [])
    if task_log:
        mcp_resource["annotations"]["task_log_entries"] = len(task_log)

    # Add FSRS stability metrics
    if skills:
        avg_stability = sum(s.get("fsrs_stability", 0) for s in skills) / len(skills)
        avg_difficulty = sum(s.get("fsrs_difficulty", 5.0) for s in skills) / len(skills)
        stale_count = sum(1 for s in skills if s.get("stale", False))
        mcp_resource["annotations"]["avg_fsrs_stability"] = avg_stability
        mcp_resource["annotations"]["avg_fsrs_difficulty"] = avg_difficulty
        mcp_resource["annotations"]["stale_skills"] = stale_count

    # Add passport age metadata
    if card_dict.get("passport_age_days") is not None:
        mcp_resource["annotations"]["passport_age_days"] = card_dict["passport_age_days"]
        mcp_resource["annotations"]["freshness_score"] = card_dict.get("freshness_score", 1.0)
        mcp_resource["annotations"]["needs_refresh"] = card_dict.get("passport_age_days", 0) > 60

    return mcp_resource
