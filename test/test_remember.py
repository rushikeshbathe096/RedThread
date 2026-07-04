import os
import asyncio
from dotenv import load_dotenv
import inspect

load_dotenv()

async def main():
    import cognee
    # Try configuring gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("Got gemini key")
        cognee.config.set_llm_provider("gemini")
        cognee.config.set_llm_model("gemini/gemini-2.0-flash")
        cognee.config.set_llm_api_key(gemini_key)
        
        # Test remember
        print("Starting remember...")
        res = await cognee.remember("Alice knows Bob", dataset_name="test_dataset")
        print("Remember result:", res)
    else:
        print("No gemini key")
        
if __name__ == "__main__":
    asyncio.run(main())
