from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RememberRequest(BaseModel):
    content: str
    source_name: str

class RememberResponse(BaseModel):
    status: str
    entities_found: int

class RecallRequest(BaseModel):
    query: str

class RecallResponse(BaseModel):
    answer: str
    raw_path: List[Dict[str, Any]]
    path: List[str] = []

class ForgetRequest(BaseModel):
    target: str
    reason: str
    confidence: float = 1.0
    query: Optional[str] = None

class ForgetResponse(BaseModel):
    status: str
    affected_edges: int
    previous_answer: Optional[str] = None
    updated_answer: Optional[str] = None
