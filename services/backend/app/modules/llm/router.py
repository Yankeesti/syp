"""API endpoints for direct LLM interaction and debugging."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, status, HTTPException

from app.modules.llm.dependencies import LLMServiceDep
from app.modules.llm.providers.base import (
    LLMProviderError,
    LLMProviderUnavailableError,
)
from app.shared.quiz_generation import QuizGenerationSpec, QuizUpsertDto

router = APIRouter(prefix="/llm", tags=["llm"])


# --- ENDPOINTS ---


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
async def check_llm_connection(
    llm_service: LLMServiceDep,
):
    """
    Diagnose-Endpunkt: Prüft, ob das Backend den LLM-Server erreicht.
    """
    try:
        return await llm_service.health_check()
    except LLMProviderUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Verbindung fehlgeschlagen: {str(e)}. VPN aktiv?",
        )
