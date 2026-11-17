import os
from dotenv import load_dotenv

load_dotenv()

COGNEE_API_KEY = os.getenv("COGNEE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not COGNEE_API_KEY:
    raise RuntimeError("Missing COGNEE_API_KEY in environment variables")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in environment variables")
