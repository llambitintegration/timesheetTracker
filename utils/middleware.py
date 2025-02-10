from fastapi import Request
from fastapi.responses import JSONResponse
from utils.logger import Logger
import time
from typing import Callable

logger = Logger().get_logger()

async def logging_middleware(request: Request, call_next: Callable):
    """Enhanced logging middleware with CORS details"""
    start_time = time.time()

    try:
        # Detailed request logging
        logger.info(f"=== Request Details ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Origin: {request.headers.get('origin', 'No origin')}")
        logger.info(f"Headers: {dict(request.headers)}")

        # Process the request
        response = await call_next(request)

        # Let FastAPI CORSMiddleware handle the CORS headers
        pass

        # Log response details
        process_time = (time.time() - start_time) * 1000
        logger.info(f"=== Response Details ===")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Processing Time: {process_time:.2f}ms")

        # Log CORS-specific headers
        cors_headers = {k: v for k, v in response.headers.items() if k.lower().startswith('access-control-')}
        if cors_headers:
            logger.info(f"CORS Headers: {cors_headers}")

        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url}")
        logger.error(f"Error details: {str(e)}")
        logger.exception("Full error traceback:")
        raise