"""
UUID validation utilities for the application.

Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Package: Kezura
"""

from __future__ import annotations

from typing import Optional, Union
import uuid


def validate_uuid(uuid_string: Union[str, uuid.UUID]) -> Optional[uuid.UUID]:
    """
    Validate and convert string to UUID.
    
    Args:
        uuid_string: String representation of UUID or UUID object
        
    Returns:
        UUID object if valid, None if invalid
    """
    if isinstance(uuid_string, uuid.UUID):
        return uuid_string
    
    try:
        return uuid.UUID(str(uuid_string))
    except (ValueError, TypeError, AttributeError):
        return None


def validate_uuid_list(uuid_strings: list[Union[str, uuid.UUID]]) -> tuple[list[uuid.UUID], list[str]]:
    """
    Validate a list of UUID strings and return valid UUIDs and invalid strings.
    
    Args:
        uuid_strings: List of UUID strings or UUID objects
        
    Returns:
        Tuple of (valid_uuids, invalid_strings)
    """
    valid_uuids = []
    invalid_strings = []
    
    for uuid_str in uuid_strings:
        validated = validate_uuid(uuid_str)
        if validated:
            valid_uuids.append(validated)
        else:
            invalid_strings.append(str(uuid_str))
    
    return valid_uuids, invalid_strings


def is_valid_uuid(uuid_string: Union[str, uuid.UUID]) -> bool:
    """
    Check if a string is a valid UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID format, False otherwise
    """
    return validate_uuid(uuid_string) is not None


def generate_uuid() -> uuid.UUID:
    """
    Generate a new UUID4.
    
    Returns:
        New UUID4 object
    """
    return uuid.uuid4()


def uuid_to_str(uuid_obj: Union[str, uuid.UUID]) -> str:
    """
    Convert UUID to string format.
    
    Args:
        uuid_obj: UUID object or string
        
    Returns:
        String representation of UUID
    """
    if isinstance(uuid_obj, uuid.UUID):
        return str(uuid_obj)
    return str(uuid_obj)


def str_to_uuid(uuid_string: str) -> Optional[uuid.UUID]:
    """
    Convert string to UUID object.
    
    Args:
        uuid_string: String representation of UUID
        
    Returns:
        UUID object if valid, None if invalid
    """
    return validate_uuid(uuid_string)
