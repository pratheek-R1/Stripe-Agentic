"""
nl_parser.py  –  Natural language → structured payment data extractor.

Uses the existing Groq API configuration from .env to parse a free-text
payment prompt into structured fields ready for the existing Stripe workflow.

Intentionally lightweight: one function, no new frameworks.
"""

import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client: Groq | None = None


def _get_client() -> Groq:
    """Lazily initialise the Groq client (reuses the existing API key)."""
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


SYSTEM_PROMPT = """\
You are a payment detail extractor. Given a natural language payment request,
extract the following fields and return ONLY a valid JSON object with no
additional text or explanation:

{
  "amount": <number, dollars, e.g. 250.00>,
  "product_name": <string, the product or service name>,
  "email": <string, customer email address>,
  "quantity": <integer, default 1 if not mentioned>
}

Rules:
- amount must be a positive number (dollars, not cents).
- If the amount includes a currency symbol ($, £, €) strip it and return the numeric value.
- product_name should be a concise description of the product or service.
- email must be a valid email address.
- quantity defaults to 1 if not specified.
- If any of amount, product_name, or email cannot be reliably extracted,
  set that field to null.
- Return ONLY the JSON object, nothing else.
"""


def extract_payment_details(prompt: str) -> dict:
    """
    Parse a natural language payment prompt into structured payment data.

    Returns a dict with keys: amount, product_name, email, quantity.
    Raises ValueError with a descriptive message if extraction fails or
    required fields are missing/invalid.
    """
    client = _get_client()

    try:
        chat = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=256,
        )
        raw = chat.choices[0].message.content.strip()
    except Exception as exc:
        raise ValueError(f"Groq API call failed: {exc}") from exc

    # Extract JSON even if the model wraps it in markdown code fences
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        raise ValueError(f"AI did not return valid JSON. Raw response: {raw!r}")

    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse AI JSON response: {exc}. Raw: {raw!r}") from exc

    # ── Validation ──────────────────────────────────────────────────────────

    errors = []

    # Amount
    amount = data.get("amount")
    if amount is None:
        errors.append("amount could not be extracted from the prompt")
    else:
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("amount must be greater than zero")
        except (TypeError, ValueError):
            errors.append(f"amount is not a valid number: {amount!r}")

    # Product name
    product_name = data.get("product_name")
    if not product_name or str(product_name).strip().lower() in ("null", "none", ""):
        errors.append("product/service name could not be extracted from the prompt")
    else:
        product_name = str(product_name).strip()

    # Email – basic RFC-style validation
    email = data.get("email")
    if not email or str(email).strip().lower() in ("null", "none", ""):
        errors.append("customer email could not be extracted from the prompt")
    else:
        email = str(email).strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append(f"extracted email is not valid: {email!r}")

    # Quantity
    quantity = data.get("quantity", 1)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    if errors:
        raise ValueError("Extraction errors: " + "; ".join(errors))

    return {
        "amount": amount,
        "product_name": product_name,
        "email": email,
        "quantity": quantity,
    }
