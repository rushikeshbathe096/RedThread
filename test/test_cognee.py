import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def main():
    import cognee
    # Trying to setup cognee config for gemini
    print(dir(cognee.config))
    try:
        from cognee.infrastructure.llm.config import get_llm_config
        config = get_llm_config()
        print(config)
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    asyncio.run(main())
