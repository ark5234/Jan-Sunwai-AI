from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from app.config import settings

logger = logging.getLogger("JanSunwaiAI.RateLimiter")
F = TypeVar("F", bound=Callable[..., Any])


class _NoopLimiter:
    """Fallback limiter used when slowapi is unavailable or disabled."""

    def limit(self, _spec: str) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            return func

        return decorator


# Public exports consumed by main.py
limiter: Any = _NoopLimiter()
RateLimitExceeded = Exception
SlowAPIMiddleware = None
_rate_limit_exceeded_handler = None
RATE_LIMITING_AVAILABLE = False

if settings.enable_rate_limiting:
    try:
        from slowapi import Limiter as _Limiter
        from slowapi import _rate_limit_exceeded_handler as _slowapi_rate_limit_handler
        from slowapi.errors import RateLimitExceeded as _RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware as _SlowAPIMiddleware
        from slowapi.util import get_remote_address

        limiter = _Limiter(key_func=get_remote_address)
        RateLimitExceeded = _RateLimitExceeded
        SlowAPIMiddleware = _SlowAPIMiddleware
        _rate_limit_exceeded_handler = _slowapi_rate_limit_handler
        RATE_LIMITING_AVAILABLE = True
    except Exception as exc:
        logger.warning(
            "RATE_LIMIT_ENABLED is true but slowapi could not be imported; running without rate limiting. err=%s",
            exc,
        )
