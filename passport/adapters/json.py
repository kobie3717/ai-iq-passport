"""Plain JSON adapter for import/export."""

import json
from typing import Dict, Any


def export_json(card_dict: Dict[str, Any], output_path: str, indent: int = 2) -> None:
    """Export agent card to JSON file.

    Args:
        card_dict: Agent card as dictionary
        output_path: Path to output JSON file
        indent: JSON indentation (default 2)
    """
    with open(output_path, "w") as f:
        json.dump(card_dict, f, indent=indent)


def import_json(input_path: str) -> Dict[str, Any]:
    """Import agent card from JSON file.

    Args:
        input_path: Path to JSON file

    Returns:
        Agent card dictionary
    """
    with open(input_path, "r") as f:
        return json.load(f)
