import os
import sys
import json
import asyncio

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.memory import recall, recall_baseline, forget, get_edge_confidences, set_edge_confidence
from backend.llm import phrase_answer

async def evaluate(answer, expected):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    prompt = f"Given the expected answer: '{expected}', does the provided answer: '{answer}' contain the correct entity/relationship and convey the correct meaning? Reply only with 'Yes' or 'No'."
    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
        )
    )
    
    return "Yes" in response.text

async def main():
    with open("backend/eval/qa_pairs.json") as f:
        qa_pairs = json.load(f)
        
    print("Running evaluation...")
    
    results = []
    
    for qa in qa_pairs:
        query = qa["question"]
        expected = qa["ground_truth"]
        
        # Baseline
        base_raw = await recall_baseline(query)
        base_ans = await phrase_answer(base_raw, query)
        base_correct = await evaluate(base_ans, expected)
        
        # Graph
        graph_raw = await recall(query)
        graph_ans = await phrase_answer(graph_raw, query)
        graph_correct = await evaluate(graph_ans, expected)
        
        results.append({
            "question": query,
            "type": qa["type"],
            "expected": expected,
            "baseline": base_ans,
            "baseline_correct": base_correct,
            "graph": graph_ans,
            "graph_correct": graph_correct
        })
        print(f"Evaluated: {query} -> Base: {base_correct}, Graph: {graph_correct}")
        
    # Aggregate
    single_hop_base = sum(1 for r in results if r["type"] == "single-hop" and r["baseline_correct"])
    single_hop_graph = sum(1 for r in results if r["type"] == "single-hop" and r["graph_correct"])
    single_hop_total = sum(1 for r in results if r["type"] == "single-hop")
    
    multi_hop_base = sum(1 for r in results if r["type"] == "multi-hop" and r["baseline_correct"])
    multi_hop_graph = sum(1 for r in results if r["type"] == "multi-hop" and r["graph_correct"])
    multi_hop_total = sum(1 for r in results if r["type"] == "multi-hop")
    
    print("\n--- MEASURED RESULTS ---")
    print(f"Single-hop accuracy (N={single_hop_total}): Baseline: {single_hop_base}/{single_hop_total}, Graph: {single_hop_graph}/{single_hop_total}")
    print(f"Multi-hop accuracy (N={multi_hop_total}): Baseline: {multi_hop_base}/{multi_hop_total}, Graph: {multi_hop_graph}/{multi_hop_total}")
    
    # Forget logic eval
    print("\n--- FORGET WORKFLOW EVAL ---")
    q = "Is there a connection between Global Trade Corp and Arthur Pendelton?"
    
    # We simulate the contradiction manually for eval purposes
    ans_before = await phrase_answer(await recall(q), q, confidences={})
    print("Answer Before Forgetting '0x9A4bC3F8D':", ans_before)
    
    # Apply a manual confidence drop that gets simulated by set_edge_confidence inside the real app
    # For eval script, let's just use the `confidences` param on phrase_answer directly
    print("Contradicting '0x9A4bC3F8D' claim...")
    ans_after = await phrase_answer(await recall(q), q, confidences={"0x9A4bC3F8D": 0.1})
    
    print("Answer After Forgetting:", ans_after)
    
if __name__ == "__main__":
    asyncio.run(main())
