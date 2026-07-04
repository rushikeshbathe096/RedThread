import os
import sys
import asyncio

async def main():
    try:
        # Import after asyncio loop starts to ensure proper context
        from backend.memory import remember, recall, forget
        from backend.llm import phrase_answer
        
        # 1. Read sample file
        data_path = os.path.join(os.path.dirname(__file__), "data", "sample_case_a.txt")
        with open(data_path, "r", encoding="utf-8") as f:
            content = f.read()

        source_name = "test_case_a_dataset"

        print(f"--- 1. Remembering Data into {source_name} ---")
        remember_res = await remember(content, source_name)
        print("Remember response:")
        print(remember_res)

        print("\n--- 2. Recalling Data ---")
        # 2-hop question
        query = "How is Julian Barnes connected to Elena Rostova?"
        recall_res = await recall(query)
        print("Recall response (raw):")
        print(recall_res)

        print("\n--- 3. Phrasing Answer ---")
        answer = await phrase_answer(recall_res, query)
        print("Phrased Answer:")
        print(answer)

        # Assertions
        assert "Julian Barnes" in answer or "Julian" in answer, "Missing 'Julian Barnes' in answer"
        assert "Elena Rostova" in answer or "Elena" in answer, "Missing 'Elena Rostova' in answer"

        print("\n--- 4. Forgetting Data ---")
        forget_res = await forget(source_name, "End of test cleanup")
        print("Forget response:")
        print(forget_res)

        print("\nSmoke test passed successfully.")
        
    except Exception as e:
        print(f"\nSmoke test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
