import time
import logging
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("paycore.middleware")

# Basit in-memory rate limiting (tek worker / demo için).
# Gerçek prodüksiyonda Redis tabanlı yapılmalı.
rate_limit_store = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()

    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if now - t < 60
    ]
    if len(rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429, content={"detail": "Too many requests"}
        )
    rate_limit_store[client_ip].append(now)
    return await call_next(request)


async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {e}", exc_info=True)
        raise
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s"
    )
    response.headers["X-Process-Time"] = str(process_time)
    return response
