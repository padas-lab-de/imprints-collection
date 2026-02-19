import json
import re


def parse_llm_response_content(content: str | None) -> dict:
    """
    Parses a string containing a JSON-like location response (possibly wrapped in code block syntax)
    and converts it into a Python dictionary. If parsing fails or no JSON is found,
    returns a default location dictionary structure.

    Args:
        response_loc (str): The string containing the location response, either in JSON format
                            or wrapped within Markdown code block (```json ... ```).

    Returns:
        dict: A dictionary containing the parsed location data. If parsing fails, returns a
              default dictionary with empty fields for Country, Town, PLZ, Street, and Streetnumber.
    """
    try:
        if content and "```" in content:
            regex = re.search(r"```(?:json\s*)?(.*?)```", content, re.DOTALL)
            if regex:
                parsed = regex.group(1).strip()
                return json.loads(parsed)

        elif content and "{" in content and "}" in content:
            regex = re.search(r"\{.*\}", content, re.DOTALL)
            if regex:
                parsed = regex.group(0).strip()
                return json.loads(parsed)
    except:
        pass

    return {
        "location_1": {
            "Country": " ",
            "Town": " ",
            "PLZ": " ",
            "Street": " ",
            "Streetnumber": " ",
        }
    }
