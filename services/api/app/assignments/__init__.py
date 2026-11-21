"""Assignments Module Exports [M3]."""

try:
    from .router import router
except ImportError:
    router = None

from .schemas import (
    AssignmentAcknowledge,
    AssignmentCreate,
    AssignmentProgress,
    AssignmentResolve,
    AssignmentResponse,
)

__all__ = [
    "router",
    "AssignmentAcknowledge",
    "AssignmentCreate",
    "AssignmentProgress",
    "AssignmentResolve",
    "AssignmentResponse",
]
