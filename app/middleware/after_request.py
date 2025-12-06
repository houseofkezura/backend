import time
from flask import Flask, request, Response
from typing import Any, cast

from app.logging import log_event
from ..extensions import db

def set_access_control_allows(response: Response) -> Response:
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type, Authorization, Origin,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS"
    )
    
    return response


def add_security_headers(response: Response) -> Response:
    """
    Function to add security headers to the response.
    Adds X-Content-Type-Options and X-Frame-Options headers.
    
    Args:
        response (Response): The response object.
    
    Returns:
        Response: The modified response object.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


def log_response(response: Response) -> Response:
    """
    Function to log details about the response.
    Logs the response status and response time.
    
    Args:
        response (Response): The response object.
    
    Returns:
        Response: The modified response object.
    """
    context = cast(dict[str, Any], getattr(request, 'context', {}))
    response_time = time.time() - context.get('start_time', time.time())
    log_event("Response INFO", data=f"Response Status: {response.status}, \nResponse Time: {response_time}")
    return response

def close_resources(response: Response) -> Response:
    """
    Function to close resources after each request.
    Closes the database session.
    
    Args:
        response (Response): The response object.
    
    Returns:
        Response: The modified response object.
    """
    db.session.close()
    return response
