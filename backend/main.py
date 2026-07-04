from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import json
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    RememberRequest, RememberResponse,
    RecallRequest, RecallResponse,
    ForgetRequest, ForgetResponse
)
from .memory import remember, recall, forget
from .llm import phrase_answer
from .graph_transform import get_flat_graph

app = FastAPI(title="Redthread Memory Core")

# Required for frontend to interact with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/remember", response_model=RememberResponse)
async def remember_endpoint(request: RememberRequest):
    result = await remember(request.content, request.source_name)
    return RememberResponse(
        status=result.get("status", "success"),
        entities_found=len(result.get("raw_result", ""))
    )

@app.post("/ingest/stream")
async def ingest_stream(file: UploadFile = File(None), text: str = Form(None), source_name: str = Form("upload")):
    async def event_generator():
        content = ""
        if file:
            content = (await file.read()).decode("utf-8")
        elif text:
            content = text
            
        if not content:
            yield f"data: {json.dumps({'type': 'error', 'data': 'No content provided'})}\n\n"
            return
            
        try:
            # Fully ingest
            await remember(content, source_name)
            
            # Extract flat graph and stream it incrementally
            graph = await get_flat_graph()
            
            for node in graph["nodes"]:
                yield f"data: {json.dumps({'type': 'node', 'data': node})}\n\n"
                await asyncio.sleep(0.15)
                
            for edge in graph["edges"]:
                yield f"data: {json.dumps({'type': 'edge', 'data': edge})}\n\n"
                await asyncio.sleep(0.15)
                
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/graph")
async def get_graph():
    return await get_flat_graph()

@app.post("/recall", response_model=RecallResponse)
async def recall_endpoint(request: RecallRequest):
    result = await recall(request.query)
    raw_path = result.get("results", [])
    
    # Extract path from raw_path
    path = []
    for item in raw_path:
        # Based on cognee's raw search result, attempt to extract node ID traversed
        # The result could be a dictionary representing a node/edge or having an id
        if isinstance(item, dict):
            if "node_id" in item:
                path.append(str(item["node_id"]))
            elif "id" in item:
                path.append(str(item["id"]))
            elif "source_node_id" in item:
                path.append(str(item["source_node_id"]))
                if "target_node_id" in item:
                    path.append(str(item["target_node_id"]))
                    
    # Ensure distinct in order
    seen = set()
    distinct_path = [x for x in path if not (x in seen or seen.add(x))]
    
    answer = await phrase_answer({"results": raw_path}, request.query)
    return RecallResponse(
        answer=answer,
        raw_path=raw_path,
        path=distinct_path
    )

@app.post("/forget", response_model=ForgetResponse)
async def forget_endpoint(request: ForgetRequest):
    result = await forget(request.target, request.reason)
    return ForgetResponse(
        status=result.get("status", "success"),
        affected_edges=result.get("affected_edges", 0)
    )
