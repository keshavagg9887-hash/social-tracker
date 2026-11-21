"""Detectors module for AI Worker [M2]."""

from .base import BaseDetector, DetectionResult

__all__ = [
    "BaseDetector",
    "DetectionResult",
    "FireDetector",
    "SmokeDetector",
    "AccidentDetector",
]

def __getattr__(name: str):
    if name == "FireDetector":
        from .fire.fire_detector import FireDetector
        return FireDetector
    elif name == "SmokeDetector":
        from .smoke.smoke_detector import SmokeDetector
        return SmokeDetector
    elif name == "AccidentDetector":
        from .accident.accident_detector import AccidentDetector
        return AccidentDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
