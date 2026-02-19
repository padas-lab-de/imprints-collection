import os

from ic.config import *


def load_prompt(task: str, language: str, prompt_type: str) -> str:
    """
    Load a prompt text from file.
    """
    prompt = os.path.join(
        PROMPTS_FOLDER,
        task,
        language,
        f"{prompt_type}.txt",
    )

    if not os.path.exists(prompt):
        raise FileNotFoundError(f"Prompt file not found: {prompt}")

    with open(prompt, "r") as f:
        return f.read()


def format_message(system_prompt, prompt):
    message = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    return message
