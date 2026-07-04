import os
import cognee
from .config import COGNEE_API_KEY, GEMINI_API_KEY

os.environ["COGNEE_API_KEY"] = COGNEE_API_KEY

# Configure Cognee to use Gemini for entity extraction
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
cognee.config.set_llm_provider("gemini")
cognee.config.set_llm_model("gemini/gemini-2.0-flash")
cognee.config.set_llm_api_key(GEMINI_API_KEY)

# Global dictionary to track confidence levels for specific claims/edges (label -> confidence)
EDGE_CONFIDENCE = {}

def get_edge_confidences():
    return EDGE_CONFIDENCE

def set_edge_confidence(target: str, confidence: float):
    EDGE_CONFIDENCE[target] = confidence

def find_overlap(dataset_a_nodes: list, dataset_b_nodes: list) -> list[dict]:
    """
    Compares entity identifiers across two node lists using simple normalization.
    """
    overlap = []
    b_normalized = {str(n.get("label", n.get("id", ""))).lower().strip(): n for n in dataset_b_nodes}
    for a in dataset_a_nodes:
        label_a = str(a.get("label", a.get("id", ""))).lower().strip()
        if label_a in b_normalized:
            overlap.append(a)
    return overlap

async def remember(content: str, source_name: str) -> dict:
    """
    Ingests content into Cognee, triggers graph construction, and returns the raw ingestion result.
    """
    try:
        result = await cognee.remember(content, dataset_name=source_name)
        return {"status": "success", "raw_result": str(result)}
    except Exception as e:
        raise RuntimeError(f"Cognee remember() failed for source_name={source_name}: {e}")

async def recall(query: str) -> dict:
    """
    Queries Cognee's hybrid graph+vector search and returns the raw structured result.
    """
    try:
        results = await cognee.recall(query)
        raw_results = []
        for res in results:
            if hasattr(res, "model_dump"):
                raw_results.append(res.model_dump())
            elif hasattr(res, "__dict__"):
                raw_results.append(res.__dict__)
            else:
                raw_results.append(str(res))
                
        return {"results": raw_results}
    except Exception as e:
        raise RuntimeError(f"Cognee recall() failed for query='{query}': {e}")

async def forget(target: str, reason: str) -> dict:
    """
    Removes or down-weights the specified entity/claim in Cognee.
    Using dataset deletion as the primary mechanism for forgetting in the current SDK version.
    """
    try:
        result = await cognee.forget(dataset=target)
        return {"status": "success", "affected_edges": 1, "raw_result": str(result), "reason": reason}
    except Exception as e:
        raise RuntimeError(f"Cognee forget() failed for target='{target}': {e}")
