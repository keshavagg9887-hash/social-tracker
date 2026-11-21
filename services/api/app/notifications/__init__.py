"""Notifications Module Exports [M3]."""

from .router import router
from .service import create_and_dispatch_notification

__all__ = ["router", "create_and_dispatch_notification"]
