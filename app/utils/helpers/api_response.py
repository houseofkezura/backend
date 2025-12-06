"""
This module defines helper functions for generating HTTP responses in the QUAS Flask application.

These functions assist with tasks such as generating success and error responses.

@author: Emmanuel Olowu
@link: https://github.com/zeddyemy

@app/utils/helpers/http_response.py
"""
from flask import jsonify, make_response, Response
from typing import Any, Dict

def error_response(msg: str, status_code: int, resp_data: dict | None = None) -> Response:
    '''
    Creates a JSON response for an error with a specified status code.

    Args:
        msg (str): The error message to include in the response.
        status_code (int): The HTTP status code for the response.
        resp_data (dict, optional): Additional data to include in the response. Defaults to None.

    Returns:
        flask.Response: A JSON response object with the error details and status code.
    '''
    payload: Dict[str, Any] = {
        "status": 'failed',
        "status_code": status_code,
        "message": msg
    }
    if resp_data:
        payload.update({"data": resp_data})
    
    response: Response = make_response(jsonify(payload))
    response.status_code = status_code
    
    return response

def success_response(msg: str, status_code: int, resp_data: dict | None = None) -> Response:
    '''
    Creates a JSON response for a success with a specified status code.

    Args:
        msg (str): The success message to include in the response.
        status_code (int): The HTTP status code for the response.
        resp_data (dict, optional): Additional data to include in the response. Defaults to None.

    Returns:
        flask.Response: A JSON response object with the success message and status code.
    '''
    payload: Dict[str, Any] = {
        "status": 'success',
        "status_code": status_code,
        "message": msg
    }
    if resp_data:
        payload.update({"data": resp_data})
    
    response: Response = make_response(jsonify(payload))
    response.status_code = status_code
    
    return response