from fastapi import Request
from utils.logger import Logger
import time
from typing import Callable

logger = Logger().get_logger()

async def log_middleware(request: Request, call_next: Callable):
    """Middleware to log request details and timing"""
    start_time = time.time()

    # Log detailed request information
    logger.info(f"Request started: {request.method} {request.url}")
    logger.info(f"Request origin: {request.headers.get('origin', 'No origin')}")
    logger.info(f"Request headers: {dict(request.headers)}")

    try:
        # Process the request
        response = await call_next(request)

        # Log response details
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Duration: {process_time:.2f}ms"
        )
        logger.info(f"Response headers: {dict(response.headers)}")

        # Special handling for CORS preflight requests
        if request.method == "OPTIONS":
            logger.info("Processing CORS preflight request")
            logger.info(f"CORS headers in response: {[h for h in response.headers.keys() if h.lower().startswith('access-control-')]}")

        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url} - Error: {str(e)}")
        logger.exception("Request processing error details:")
        raise