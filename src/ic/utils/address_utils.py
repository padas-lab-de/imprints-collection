from typing import Any


def has_address(address: Any) -> bool:
    """
    True if the address is a dict with at least one non-empty field.

    An LLM answer whose fields are all None or empty strings is no address.
    """
    if not isinstance(address, dict):
        return False
    return any(
        value is not None and str(value).strip() != "" for value in address.values()
    )
