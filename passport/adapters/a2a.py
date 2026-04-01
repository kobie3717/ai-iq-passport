"""Google A2A Agent Card format adapter.

Reference: https://github.com/a2aproject/A2A
"""

from typing import Dict, Any, List


def export_a2a(card_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Export agent card to Google A2A Agent Card format.

    Args:
        card_dict: Agent card dictionary

    Returns:
        A2A-compatible agent card dictionary
    """
    # Extract skills and build capabilities
    skills = card_dict.get("skills", [])
    capabilities = []

    for skill in skills:
        capability = {
            "name": skill["name"],
            "confidence": skill.get("confidence", 0.5),
            "description": f"Skill: {skill['name']}",
        }

        if skill.get("tags"):
            capability["tags"] = skill["tags"]

        if skill.get("evidence_count"):
            capability["evidence_count"] = skill["evidence_count"]

        # Add FSRS stability, difficulty, and decay info
        if skill.get("fsrs_stability"):
            capability["fsrs_stability"] = skill["fsrs_stability"]

        if skill.get("fsrs_difficulty"):
            capability["fsrs_difficulty"] = skill["fsrs_difficulty"]

        if skill.get("decayed_confidence"):
            capability["decayed_confidence"] = skill["decayed_confidence"]

        if skill.get("stale"):
            capability["stale"] = skill["stale"]

        capabilities.append(capability)

    # Build A2A card
    a2a_card = {
        "@context": "https://a2aproject.org/schema",
        "@type": "AgentCard",
        "id": card_dict["agent_id"],
        "name": card_dict["name"],
        "description": f"AI agent with {len(skills)} skills",
        "version": card_dict.get("version", "0.1.0"),
        "created": card_dict["created_at"],
        "updated": card_dict["updated_at"],
        "capabilities": capabilities,
    }

    # Add reputation if available
    reputation = card_dict.get("reputation")
    if reputation:
        a2a_card["reputation"] = {
            "score": reputation["overall_score"],
            "feedback_score": reputation["feedback_score"],
            "prediction_accuracy": reputation["prediction_accuracy"],
            "task_completion_rate": reputation["task_completion_rate"],
            "total_tasks": reputation.get("total_tasks", 0),
        }

    # Add task history
    task_history = card_dict.get("task_history")
    if task_history and task_history.get("total_tasks", 0) > 0:
        a2a_card["task_history"] = {
            "total": task_history["total_tasks"],
            "completed": task_history["completed_tasks"],
            "success_rate": task_history["success_rate"],
        }

    # Add traits as metadata
    traits = card_dict.get("traits", {})
    if traits:
        a2a_card["metadata"] = traits

    # Add predictions if available
    predictions = card_dict.get("predictions", [])
    if predictions:
        a2a_card["predictions"] = predictions

    # Add task log summary
    task_log = card_dict.get("task_log", [])
    if task_log:
        # Provide summary instead of full log
        success_count = sum(1 for t in task_log if t.get("outcome") == "success")
        a2a_card["task_log_summary"] = {
            "total_tasks": len(task_log),
            "success_rate": success_count / len(task_log) if task_log else 0.0,
            "recent_tasks": task_log[:10] if len(task_log) > 10 else task_log,
        }

    # Add passport age metadata
    if card_dict.get("passport_age_days") is not None:
        a2a_card["passport_metadata"] = {
            "age_days": card_dict["passport_age_days"],
            "stale_skills_count": card_dict.get("stale_skills_count", 0),
            "freshness_score": card_dict.get("freshness_score", 1.0),
            "last_refreshed": card_dict.get("last_refreshed"),
        }

    # Add signature for verification
    if card_dict.get("signature"):
        a2a_card["signature"] = card_dict["signature"]

    return a2a_card
