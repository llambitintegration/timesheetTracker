from fastapi import Request
from utils.logger import Logger
import time
from typing import Callable

logger = Logger().get_logger()

async def log_middleware(request: Request, call_next: Callable):
    """Middleware to log request details and timing"""
    start_time = time.time()

    # Log essential request information
    logger.info(f"Request started: {request.method} {request.url}")
    logger.info(f"Request origin: {request.headers.get('origin', 'No origin')}")

    try:
        # Process the request
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