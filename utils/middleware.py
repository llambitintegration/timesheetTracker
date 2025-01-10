from fastapi import Request, Response
from utils.logger import Logger
import time
from typing import Callable
from fastapi.middleware.cors import CORSMiddleware

logger = Logger().get_logger()

async def log_middleware(request: Request, call_next: Callable):
    """Middleware to log request details and timing"""
    start_time = time.time()

    # Log detailed request information
    logger.info(f"Request started: {request.method} {request.url}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request origin: {request.headers.get('origin')}")

    try:
        # Special handling for OPTIONS requests
        if request.method == "OPTIONS":
            logger.debug("Handling OPTIONS request with CORS headers")
            response = Response(
                content="",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                }
            )
        else:
            # Process non-OPTIONS requests
            response = await call_next(request)

        # Log response details
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Duration: {process_time:.2f}ms"
        )

        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url} - Error: {str(e)}")
        logger.exception("Request processing error details:")
        raise