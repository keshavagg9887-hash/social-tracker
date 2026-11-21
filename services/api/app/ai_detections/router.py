"""AI Detections API Router [M2].

Endpoints for receiving, inspecting, and managing AI-generated event candidates.
"""

from typing import List
from collections import deque
from fastapi import APIRouter, HTTPException, status
from .schemas import AIDetectionEventCandidate, AIDetectionResponse

router = APIRouter(prefix="/ai-detections", tags=["AI Detections"])

# In-memory circular buffer for the most recent 100 AI event candidates
# (Used for quick verification, fallback monitoring, and integration tests)
_recent_candidates = deque(maxlen=100)


@router.post(
    "/events",
    response_model=AIDetectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest AI Event Candidate",
    description="Endpoint for AI worker to publish fire, smoke, or road accident candidates.",
)
async def ingest_ai_candidate(candidate: AIDetectionEventCandidate) -> AIDetectionResponse:
    """Receives an event candidate from the AI worker and records it."""
    # Store in recent buffer
    _recent_candidates.appendleft(candidate.model_dump())

    # Return acknowledgement
    return AIDetectionResponse(
        status="received",
        event_id=candidate.event_id,
        message=f"Candidate [{candidate.detection_type.value}] for camera {candidate.camera_id} queued for verification",
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
