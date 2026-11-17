import asyncio
import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.memory import remember

async def main():
    with open("backend/data/sample_case_a.txt", "r") as f:
        case_a = f.read()
    with open("backend/data/sample_case_b.txt", "r") as f:
        case_b = f.read()

    print("Ingesting Case A...")
    await remember(case_a, "case_a")
    print("Ingesting Case B...")
    await remember(case_b, "case_b")
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(main())
