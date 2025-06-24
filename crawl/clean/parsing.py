"""Parsing and conversion utilities for data extraction."""

import json
import re


def extract_description(response_text: str) -> str:
    """Extract a clean description from the LLM response.

    Args:
        response_text: Raw response text from the LLM

    Returns:
        Extracted description or truncated text if extraction fails
    """
    try:
        if response_text.startswith("```json"):
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                if "description" in data:
                    return data["description"]

            data = json.loads(response_text)
            if "description" in data:
                return data["description"]

        return response_text[:200] + ("..." if len(response_text) > 200 else "")

    except Exception as e:
        print(f"Error extracting description: {e}")
        return response_text[:200] + ("..." if len(response_text) > 200 else "")

