"""
Pydantic schemas for the application.

Define request/response contracts here. Stubs provided for future expansion.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr

# Import all schemas for easy access
from .auth import *
from .response import *
from .orders import *
from .offers import *
from .payments import *
from .esim import *
from .profile import *


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    name: str
    version: str
    env: str
