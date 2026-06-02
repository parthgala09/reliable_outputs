import json
import logging
import os
from typing import Any

import openai

from models import ContactCard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_contact_card_function_schema() -> dict[str, Any]:
    return {
        "name": "submit_contact_card",
        "description": "Submit a parsed contact card with validated fields.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Person's full name."},
                "email": {"type": "string", "format": "email", "description": "Contact email address."},
                "phone": {"type": "string", "description": "10-digit phone number."},
                "address": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name."},
                        "pincode": {"type": "string", "description": "Postal code or pincode."},
                    },
                    "required": ["city", "pincode"],
                },
            },
            "required": ["name", "email", "phone", "address"],
        },
    }


def build_initial_prompt(user_input: str) -> str:
    return (
        "Extract the contact information from the text below. "
        "Return only a JSON object matching the ContactCard schema. "
        "The object must include name, email, phone, and address.city/address.pincode.\n\n"
        f"Input text:\n{user_input.strip()}"
    )


def build_repair_prompt(user_input: str, previous_output: str, validation_error: str) -> str:
    return (
        "The previous output did not validate against the ContactCard schema. "
        "Please correct the JSON output. \n\n"
        "Original request:\n"
        f"{user_input.strip()}\n\n"
        "Previous output:\n"
        f"{previous_output.strip()}\n\n"
        "Validation error:\n"
        f"{validation_error.strip()}\n\n"
        "Return only the corrected JSON object with name, email, phone, and address.city/address.pincode."
    )


def call_openai_with_schema(prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.0) -> str:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")

    functions = [build_contact_card_function_schema()]
    messages = [{"role": "user", "content": prompt}]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        functions=functions,
        function_call={"name": "submit_contact_card"},
        temperature=temperature,
    )

    message = response.choices[0].message
    if message.get("function_call"):
        return message["function_call"]["arguments"]

    # Fallback: return assistant text if function call did not occur
    return message.get("content", "")


def parse_contact_card(raw_text: str) -> ContactCard:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Response is not valid JSON: {exc}") from exc

    return ContactCard(**payload)


def repair_loop(user_input: str, model: str = "gpt-4o-mini", max_retries: int = 3) -> ContactCard:
    prompt = build_initial_prompt(user_input)
    last_output = ""
    last_error = ""

    for attempt in range(1, max_retries + 1):
        logger.info("Attempt %s for input: %s", attempt, user_input[:80])
        raw_result = call_openai_with_schema(prompt, model=model)
        last_output = raw_result

        try:
            return parse_contact_card(raw_result)
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Validation failed on attempt %s: %s", attempt, last_error)
            if attempt == max_retries:
                break
            prompt = build_repair_prompt(user_input, raw_result, last_error)

    raise ValueError(
        f"Failed to parse ContactCard after {max_retries} attempts. "
        f"Last output: {last_output}\nLast error: {last_error}"
    )
