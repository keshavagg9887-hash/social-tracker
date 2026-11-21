"""AI Detections API Router [M2/M3 Integration].

Endpoints for receiving, inspecting, and managing AI-generated event candidates.
Integrates directly with the Incident Engine [M3] for deduplication and correlation.
"""

from collections import deque
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db
from ..incidents.engine import IncidentEngine
from .schemas import AIDetectionEventCandidate, AIDetectionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-detections", tags=["AI Detections"])

# In-memory circular buffer for recent AI event candidates
_recent_candidates = deque(maxlen=100)


@router.post(
    "/events",
    response_model=AIDetectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest AI Event Candidate",
    description="Endpoint for AI worker to publish fire, smoke, or road accident candidates.",
)
async def ingest_ai_candidate(
    candidate: AIDetectionEventCandidate,
    db: AsyncSession = Depends(get_db),
) -> AIDetectionResponse:
    """Receives an event candidate from the AI worker and feeds it to the Incident Engine."""
    # Store in recent buffer
    candidate_dict = candidate.model_dump()
    _recent_candidates.appendleft(candidate_dict)

    # Process through Incident Engine
    try:
        incident, is_new = await IncidentEngine.process_candidate(db, candidate_dict)
        action_desc = "created as new incident" if is_new else "correlated into active incident"
        msg = f"Candidate [{candidate.detection_type.value}] for camera {candidate.camera_id} {action_desc} ({incident.id})"
    except Exception as e:
        logger.error(f"Error processing AI candidate through Incident Engine: {e}")
        msg = f"Candidate [{candidate.detection_type.value}] for camera {candidate.camera_id} queued for verification"

    return AIDetectionResponse(
        status="received",
        event_id=candidate.event_id,
        message=msg,
    )


@router.get(
    "/events",
    response_model=List[AIDetectionEventCandidate],
    summary="List Recent AI Detection Candidates",
    description="Returns the most recent AI detection candidates stored in buffer.",
)
async def list_recent_candidates() -> List[AIDetectionEventCandidate]:
    """Retrieves recent candidates."""
    return [AIDetectionEventCandidate(**c) for c in _recent_candidates]


@router.get(
    "/health",
    summary="AI Detection Ingestion Health Check",
)
async def ai_detection_health():
    """Health status check for AI detections intake service."""
    return {
        "status": "healthy",
        "module": "ai_detections",
        "buffered_candidates": len(_recent_candidates),
        "supported_detection_types": ["fire", "smoke", "accident"],
    }
