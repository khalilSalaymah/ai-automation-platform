"""AIOps routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.aiops_service import AiOpsService

router = APIRouter()


class AiOpsRequest(BaseModel):
    query: str
    metrics: dict = {}


@router.post("/analyze")
async def analyze(request: AiOpsRequest):
    try:
        service = AiOpsService()
        result = await service.analyze(request.query, request.metrics)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

