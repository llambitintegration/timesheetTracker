from fastapi import Request
from fastapi.responses import JSONResponse
from utils.logger import Logger, structured_log
import time
from typing import Callable
import traceback

logger = Logger().get_logger()

async def logging_middleware(request: Request, call_next: Callable):
    """Enhanced logging middleware with structured logging and request tracking"""
    start_time = time.time()
    correlation_id = Logger().set_correlation_id()

    try:
        # Detailed request logging with structured format
        logger.info(structured_log(
            "Incoming request",
            correlation_id=correlation_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else None,
            headers=dict(request.headers),
            path_params=request.path_params,
            query_params=dict(request.query_params),
            request_id=request.headers.get('x-request-id')
        ))

        # Process the request
        response = await call_next(request)

        # Log response details
        process_time = (time.time() - start_time) * 1000
        logger.info(structured_log(
            "Request completed",
            correlation_id=correlation_id,
            status_code=response.status_code,
            process_time_ms=f"{process_time:.2f}",
            response_headers=dict(response.headers),
            content_type=response.headers.get('content-type')
        ))

        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        return response

    except Exception as e:
        # Enhanced error logging
        error_details = {
            'correlation_id': correlation_id,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'request_method': request.method,
            'request_url': str(request.url),
            'request_headers': dict(request.headers),
            'client_host': request.client.host if request.client else None
        }

        logger.error(structured_log(
            "Request failed",
            **error_details
        ))

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "correlation_id": correlation_id
            }
        )

async def error_logging_middleware(request: Request, call_next: Callable):
    """Additional middleware for catching and logging unhandled exceptions"""
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(structured_log(
            "Unhandled exception",
            correlation_id=Logger().get_correlation_id(),
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc()
        ))
        raise