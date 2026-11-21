"""Auth Module Exports [M3]."""

try:
    from .router import router
except ImportError:
    router = None

from .security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    get_password_hash,
    require_roles,
    verify_password,
)

__all__ = [
    "router",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_password_hash",
    "require_roles",
    "verify_password",
]
