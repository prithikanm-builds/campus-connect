"""Gemini extraction adapter. API key is read from GEMINI_API_KEY in .env."""
import json
import os
import re
from google import genai
from google.genai import types

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "system_prompt.txt")

def load_system_prompt():
    with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        return f.read()

def extract_registration(entry, model=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to the .env file.")
    client = genai.Client(api_key=api_key)
    prompt = load_system_prompt() + "\n\nRegistration entry to extract:\n" + entry
    response = client.models.generate_content(
        model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )
    raw = (response.text or "").strip()
    data = json.loads(raw)
    required = {"name", "phone", "email", "year", "branch"}
    if not isinstance(data, dict) or set(data.keys()) != required:
        raise ValueError("Gemini response must be a JSON object with exactly five required fields.")
    return data
