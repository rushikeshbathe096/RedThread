from fastapi import FastAPI
from .models import (
    RememberRequest, RememberResponse,
    RecallRequest, RecallResponse,
    ForgetRequest, ForgetResponse
)
from .memory import remember, recall, forget
from .llm import phrase_answer

app = FastAPI(title="Redthread Memory Core")

@app.post("/remember", response_model=RememberResponse)
async def remember_endpoint(request: RememberRequest):
    result = await remember(request.content, request.source_name)
    return RememberResponse(
        status=result.get("status", "success"),
        entities_found=len(result.get("raw_result", ""))
    )

@app.post("/recall", response_model=RecallResponse)
async def recall_endpoint(request: RecallRequest):
    result = await recall(request.query)
    raw_path = result.get("results", [])
    
    answer = await phrase_answer({"results": raw_path}, request.query)
    return RecallResponse(
        answer=answer,
        raw_path=raw_path
    )

@app.post("/forget", response_model=ForgetResponse)
async def forget_endpoint(request: ForgetRequest):
    result = await forget(request.target, request.reason)
    return ForgetResponse(
        status=result.get("status", "success"),
        affected_edges=result.get("affected_edges", 0)
    )
