"""Base schema module for consistent API response structures.

This module defines generic pydantic models representing standardized responses
across all routes: {success: bool, data: any, message: str}.
"""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard generic API response wrapper.

    Attributes:
        success (bool): Indicates if the operation was successful.
        data (Optional[T]): Payload returned from the operation. Defaults to None.
        message (str): Explanatory summary message.
    """
    success: bool
    data: Optional[T] = None
    message: str
