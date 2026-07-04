import os
from google import genai
from .config import GEMINI_API_KEY

# Using google-genai package
client = genai.Client(api_key=GEMINI_API_KEY)

async def phrase_answer(raw_result: dict, query: str) -> str:
    """
    Phrases a natural language answer based on the raw structured result and the original query.
    """
    prompt = f"""
Only use the relationships provided below. Do not infer or add new connections.

Query: {query}
Raw result: {raw_result}
"""
    response = await client.aio.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    return response.text
