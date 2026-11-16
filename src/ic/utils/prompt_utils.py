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


def truncate_text(text, tokenizer, max_tokens=30_000):
    """
    Smart text truncation to fit within max token limits.
    """
    tokens = tokenizer(text)["input_ids"]

    if len(tokens) <= max_tokens:
        return text

    # Truncate the rear part of the text
    truncated_tokens = tokens[:max_tokens]
    truncated_text = tokenizer.decode(truncated_tokens, skip_special_tokens=True)

    return truncated_text + "\n[TEXT TRUNCATED]"


def prepare_content(content: str, tokenizer, max_tokens: int) -> str:
    """
    Removes newlines from the page content and truncates it to max_tokens.
    """
    return truncate_text(content.replace("\n", ""), tokenizer, max_tokens=max_tokens)


def build_address_message(system_prompt: str, prompt: str, content: str) -> list:
    """
    Builds the chat messages for the address extraction of a prepared imprint text.
    """
    return format_message(system_prompt, prompt.format(plain_text=content))


def build_topic_message(
    system_prompt: str,
    prompt: str,
    url: str,
    title: str,
    description: str,
    content: str,
) -> list:
    """
    Builds the chat messages for the topic classification of a prepared page text.
    """
    return format_message(
        system_prompt,
        prompt.format(
            url=url, title=title, description=description, plain_text=content
        ),
    )
