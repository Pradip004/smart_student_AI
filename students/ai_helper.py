"""Gemma (via Ollama) turns a question into JSON filters.
The output is untrusted: it is checked against an allowlist and never used as SQL."""
import json
import re

import requests
from django.conf import settings


class AIServiceError(Exception):
    pass


PROMPT_TEMPLATE = """You convert a question about students into a JSON filter object.
Reply with ONE JSON object only. No explanation, no markdown.

Allowed keys (omit any key the question does not mention):
- "department": string (e.g. "CSE")
- "class_name": string
- "roll_number": string (full or partial)
- "name": string (full or partial)
- "marks_gt": number 0-100 (marks greater than)
- "marks_lt": number 0-100 (marks less than)
- "attendance_gt": number 0-100
- "attendance_lt": number 0-100
- "fees_paid": true or false (true = paid, false = pending)
- "limit": integer
- "export_format": "xlsx", "docx" or "pdf" (only if a file is requested)

Examples:
Question: Find CSE students with marks above 80
{{"department": "CSE", "marks_gt": 80}}
Question: Show students with attendance below 75 percent
{{"attendance_lt": 75}}
Question: Show students with pending fees
{{"fees_paid": false}}
Question: Find Priya in ECE
{{"name": "Priya", "department": "ECE"}}

Question: {question}
"""

TEXT_KEYS = {"department": 80, "class_name": 40, "roll_number": 30, "name": 120}
NUMBER_KEYS = ("marks_gt", "marks_lt", "attendance_gt", "attendance_lt")
EXPORT_FORMATS = ("xlsx", "docx", "pdf")


def ask_gemma(question):
    payload = {"model": settings.OLLAMA_MODEL,
               "prompt": PROMPT_TEMPLATE.format(question=question.strip()),
               "stream": False, "format": "json", "options": {"temperature": 0}}
    try:
        response = requests.post(settings.OLLAMA_URL, json=payload,
                                 timeout=settings.OLLAMA_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise AIServiceError("Cannot reach the AI service. Make sure Ollama is running.")
    except requests.exceptions.Timeout:
        raise AIServiceError("The AI service took too long to respond. Please try again.")
    except requests.exceptions.RequestException:
        raise AIServiceError("Unexpected problem while contacting the AI service.")

    if response.status_code == 404:
        raise AIServiceError(f"Model '{settings.OLLAMA_MODEL}' not found. "
                             f"Run 'ollama pull {settings.OLLAMA_MODEL}'.")
    if response.status_code != 200:
        raise AIServiceError(f"AI service error (HTTP {response.status_code}).")
    try:
        text = response.json().get("response", "")
    except ValueError:
        raise AIServiceError("The AI service sent an unreadable reply.")
    return parse_model_json(text)


def parse_model_json(text):
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        match = re.search(r"\{.*\}", text or "", re.DOTALL)
        if not match:
            raise AIServiceError("The AI did not return a usable answer. Try rephrasing.")
        try:
            data = json.loads(match.group(0))
        except ValueError:
            raise AIServiceError("The AI did not return a usable answer. Try rephrasing.")
    if not isinstance(data, dict):
        raise AIServiceError("The AI did not return a usable answer. Try rephrasing.")
    return data


def validate_filters(raw):
    """Returns (clean_filters, warnings). Unknown keys and bad values are dropped."""
    max_results = getattr(settings, "AI_MAX_RESULTS", 200)
    default_limit = getattr(settings, "AI_DEFAULT_LIMIT", 50)
    clean, warnings = {}, []

    for key, value in raw.items():
        if value is None or value == "":
            continue
        if key in TEXT_KEYS:
            if isinstance(value, (str, int)) and not isinstance(value, bool):
                text = str(value).strip()[: TEXT_KEYS[key]]
                if text:
                    clean[key] = text
                    continue
            warnings.append(f"Ignored invalid value for '{key}'.")
        elif key in NUMBER_KEYS:
            try:
                if isinstance(value, bool):
                    raise ValueError
                number = float(value)
            except (TypeError, ValueError):
                warnings.append(f"Ignored non-numeric value for '{key}'.")
                continue
            if not 0 <= number <= 100:
                warnings.append(f"Ignored out-of-range value for '{key}' (must be 0-100).")
                continue
            clean[key] = number
        elif key == "fees_paid":
            if isinstance(value, bool):
                clean[key] = value
            elif isinstance(value, str) and value.strip().lower() in ("true", "false"):
                clean[key] = value.strip().lower() == "true"
            else:
                warnings.append("Ignored invalid value for 'fees_paid'.")
        elif key == "limit":
            try:
                if isinstance(value, bool):
                    raise ValueError
                clean[key] = max(1, min(int(float(value)), max_results))
            except (TypeError, ValueError):
                warnings.append("Ignored invalid value for 'limit'.")
        elif key == "export_format":
            if isinstance(value, str) and value.strip().lower() in EXPORT_FORMATS:
                clean[key] = value.strip().lower()
        else:
            warnings.append(f"Ignored unsupported filter '{key}'.")

    clean.setdefault("limit", min(default_limit, max_results))
    return clean, warnings