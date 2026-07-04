# Redthread: A self-improving institutional memory engine for complex investigations

Redthread is not just another data vault. You might ask, **"Why not Palantir?"** While systems like Palantir excel at storing and querying vast lakes of static evidence, Redthread is designed to *learn* and *forget*. It acts as a living, self-improving memory engine—it learns from every new case, automatically surfaces hidden overlaps across disparate investigations, and crucially, it explicitly "forgets" or degrades the confidence of claims when they are contradicted. 

Built for the **Cognee "Hangover" hackathon (WeMakeDevs × Cognee)**, Redthread leverages Cognee Cloud to maintain a resilient, graph-backed intelligence layer.

## Architecture Lifecycle

The core loop of Redthread is **Remember → Graph → Recall → Forget**.

```mermaid
graph TD
    A[Remember] -->|Extract entities & claims| B[Cognee Graph Engine]
    B -->|Stream visual updates| C[Live Graph View]
    C -->|Detect cross-case overlap| D[Multi-hop Recall]
    D -->|Investigator contradicts claim| E[Forget / Decay Confidence]
    E -.->|Updates prior answers| B
```

1. **Remember**: Unstructured text (investigation notes, police reports) is ingested. Entities and relationships are extracted and stored persistently in Cognee.
2. **Graph**: The frontend streams the ingestion process live, dynamically assembling a force-directed graph. Cross-case overlaps are detected and pulsed visually.
3. **Recall**: Investigators can ask multi-hop questions. The engine traverses the knowledge graph and highlights the exact reasoning path used to formulate the answer.
4. **Forget**: When an investigator marks a claim as contradicted, the engine doesn't just delete it. It decays the confidence of the edge, visually fading it on the graph, and dynamically updates previously provided answers on re-query.

## Project Structure

- `backend/`: FastAPI server handling ingestion, streaming, overlap detection, and the Cognee memory loop.
- `frontend/`: Next.js 15 application (App Router, Tailwind CSS, React Force Graph 2D).
- `test/`: End-to-end smoke tests verifying the graph memory survives cold restarts and correctly identifies cross-case overlap.

## Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- [Cognee Cloud API Key](https://cognee.ai/)
- Gemini API Key

### 1. Environment Setup

Copy the environment templates and insert your keys:

```bash
# In the root directory
cp backend/.env.example .env

# Edit .env with your keys:
# COGNEE_API_KEY=your_cognee_key
# GEMINI_API_KEY=your_gemini_key
```

### 2. Backend Installation & Run

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt

# Run the FastAPI server
uvicorn backend.main:app --reload
```

### 3. Frontend Installation & Run

Open a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:3000`.

## Running the Demo (The 5-Scene Sequence)

1. **Cold Open**: Start the frontend and backend. Ensure the graph is empty.
2. **Live Ingest**: Drag and drop (or paste) `backend/data/sample_case_a.txt` into the Ingest Panel. Watch the graph visibly assemble.
3. **Multi-Hop Recall**: Ask a complex question in the Recall Panel (e.g., *"How is Julian Barnes connected to Geneva?"*). Watch the traversal path highlight in white on the graph.
4. **Cross-Case Reveal**: Ingest `backend/data/sample_case_b.txt`. The system will automatically detect the shared wallet address (`0x9A4bC3F8D`), pulsing the node to show that institutional memory successfully linked the two isolated cases.
5. **Intelligent Forgetting**: In the Evidence Panel, click "Contradict" on a specific claim. Watch the claim's edge fade out (confidence decay) and observe the answer dynamically change when queried again.

## Verification: No Hangover

To prove the "no hangover" requirement:
1. Stop the `uvicorn` backend server.
2. Restart it.
3. Reload the frontend page. 
4. The graph and all institutional memory will persist, pulled directly from Cognee Cloud.

## AI Assistant Disclosure

Per the hackathon rules, this project was developed with the assistance of an AI coding agent (Cursor / Claude / Gemini) for scaffolding, writing boilerplate components, generating tests, and iterating on the graph logic. The core architecture, prompt design, feature constraints, and orchestration were driven by the human developer.

## Submission Details

- **Track**: Cognee Cloud
- **Video Walkthrough**: *(Insert YouTube link here prior to submission)*
