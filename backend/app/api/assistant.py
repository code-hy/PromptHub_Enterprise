"""Prompt Assistant API (spec 43)."""

from fastapi import APIRouter, Depends

from ..database import get_db
from ..models import User
from ..schemas.api import AssistantRequest, AssistantResponse
from ..security import get_current_user
from ..services import assistant_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/analyse", response_model=AssistantResponse)
def analyse(data: AssistantRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    return assistant_service.analyse(data.prompt, "analyse")


@router.post("/improve", response_model=AssistantResponse)
def improve(data: AssistantRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    return assistant_service.analyse(data.prompt, "improve")


@router.post("/generate", response_model=AssistantResponse)
def generate(data: AssistantRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    return assistant_service.analyse(data.prompt, "generate", data.business_function, data.task)


@router.post("/explain", response_model=AssistantResponse)
def explain(data: AssistantRequest, db=Depends(get_db), user: User = Depends(get_current_user)):
    return assistant_service.analyse(data.prompt, "explain")
