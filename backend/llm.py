import os
from google import genai
from .config import GEMINI_API_KEY

# Using google-genai package
client = genai.Client(api_key=GEMINI_API_KEY)

async def phrase_answer(raw_result: dict, query: str, confidences: dict = None) -> str:
    """
    Phrases a natural language answer based on the raw structured result and the original query.
    """
    prompt = f"""
Only use the relationships provided below. Do not infer or add new connections.
If a relationship has a confidence score provided and it is low (<= 0.4), treat it as a contradicted or unreliable claim and explicitly state that it is contested or false in your answer.

Query: {query}
Raw result: {raw_result}
Known relationship confidences (0.0 to 1.0): {confidences or {}}
"""
    response = await client.aio.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt
    )
    return response.text
