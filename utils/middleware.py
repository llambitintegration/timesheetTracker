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
    correlation_id = Logger().get_correlation_id() or Logger().set_correlation_id()

    try:
        # Log preflight requests specifically
        if request.method == "OPTIONS":
            logger.info(structured_log(
                "CORS preflight request",
                correlation_id=correlation_id,
                method=request.method,
                url=str(request.url),
                origin=request.headers.get("origin"),
                access_control_request_method=request.headers.get("access-control-request-method"),
                access_control_request_headers=request.headers.get("access-control-request-headers"),
                query_params=dict(request.query_params),
                path=request.url.path
            ))

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
            request_id=request.headers.get('x-request-id'),
            path=request.url.path
        ))

        # Process the request
        response = await call_next(request)

        # Log response details
        process_time = (time.time() - start_time) * 1000
        status_code = response.status_code

        # Enhanced logging for all non-200 responses
        if status_code != 200:
            log_level = "error" if status_code >= 500 else "warning"
            log_context = {
                "correlation_id": correlation_id,
                "status_code": status_code,
                "method": request.method,
                "url": str(request.url),
                "process_time_ms": f"{process_time:.2f}",
                "response_headers": dict(response.headers),
                "error_detail": response.headers.get("x-error-detail"),
                "query_params": dict(request.query_params),
                "path_params": request.path_params,
                "client_host": request.client.host if request.client else None,
                "path": request.url.path,
                "origin": request.headers.get("origin"),
                "cors_method": request.headers.get("access-control-request-method"),
                "cors_headers": request.headers.get("access-control-request-headers")
            }

            if request.method == "OPTIONS":
                log_context["request_type"] = "CORS Preflight"

            getattr(logger, log_level)(structured_log(
                f"Request failed with status {status_code}",
                **log_context
            ))
        else:
            logger.info(structured_log(
                "Request completed successfully",
                correlation_id=correlation_id,
                status_code=status_code,
                process_time_ms=f"{process_time:.2f}",
                response_headers=dict(response.headers),
                content_type=response.headers.get('content-type'),
                method=request.method,
                path=request.url.path
            ))

        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id
        return response

    except Exception as e:
        # Enhanced error logging with more context
        error_details = {
            'correlation_id': correlation_id,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc(),
            'request_method': request.method,
            'request_url': str(request.url),
            'request_headers': dict(request.headers),
            'client_host': request.client.host if request.client else None,
            'query_params': dict(request.query_params),
            'path_params': request.path_params,
            'path': request.url.path,
            'origin': request.headers.get("origin"),
            'cors_method': request.headers.get("access-control-request-method"),
            'cors_headers': request.headers.get("access-control-request-headers")
        }

        logger.error(structured_log(
            "Request failed with exception",
            **error_details
        ))

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "correlation_id": correlation_id,
                "type": type(e).__name__
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
            traceback=traceback.format_exc(),
            path=request.url.path,
            method=request.method,
            query_params=dict(request.query_params)
        ))
        raise