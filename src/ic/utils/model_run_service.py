import json
import logging
from typing import Literal

import instructor
from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from ic.config import *


class Address(BaseModel):
    country: str
    town: str
    postalcode: str
    streetname: str
    housenumber: str


class Topic(BaseModel):
    thema: Literal[*TOPICS]  # type: ignore


def call_api(
    model: str,
    prompt: str,
    prompt_type: str,
    api_endpoint: str,
    api_key: str,
    temperature: float = 0.0,
    max_tokens: int = 2_000,
) -> ChatCompletion | None:
    """
    Calls an LLM API with the provided prompts and returns the response content.

    Args:
        model (str): The name of the LLM model to use.
        user_prompt (str): The user prompt content.
        system_prompt (str): The system prompt content.
        api_key (str): The API key for authentication.
        base_url (str): The base URL for the API endpoint.
        tempretaur (float, optional): Controls the models temperatur. Defaults to 0.3.
        max_tokens (int, optional): Contains the models max. tokens. Defaults to 2000.

    Returns:
        str | None: The response ChatCompletion from the LLM, or None if an error occurs.
    """
    try:
        # Create client object
        client = OpenAI(base_url=api_endpoint, api_key=api_key)
        client = instructor.from_openai(client, mode=instructor.Mode.JSON)

        _, chat_completion = client.chat.completions.create_with_completion(
            messages=prompt,  # type: ignore
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_model=Address if prompt_type == "address" else Topic,
        )

        # Return only the whole chat_completions if true
        return chat_completion if chat_completion else None

    # Error handling
    except OpenAIError as e:
        logging.error(f"OpenAI API Error: {e}")
    except TimeoutError as e:
        logging.error(f"Timeout: {e}")
    except Exception as e:
        logging.error(f"Unknown Error: {e}")
