"""Utilities for parsing request bodies with proper error handling.

This module provides utilities to handle both JSON and Form data in POST requests,
with explicit error handling that doesn't silently swallow parsing failures.
"""

from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError


class ParsedRequest[T: BaseModel]:
    """Result of parsing a request body.

    Either contains a successfully parsed model, or an error response to return.
    """

    def __init__(
        self,
        *,
        model: T | None = None,
        error: JSONResponse | None = None,
    ) -> None:
        self.model = model
        self.error = error

    @property
    def ok(self) -> bool:
        """Return True if parsing succeeded."""
        return self.model is not None and self.error is None


def error_response(error_code: int, description: str) -> JSONResponse:
    """Create a Telegram-style error response.

    Args:
        error_code: The Telegram error code (also used as HTTP status code).
        description: The error description.

    Returns:
        JSONResponse with the error details and appropriate HTTP status code.
    """
    return JSONResponse(
        status_code=error_code,
        content={
            "ok": False,
            "error_code": error_code,
            "description": description,
        },
    )


async def parse_json_body[T: BaseModel](
    request: Request,
    model_class: type[T],
) -> ParsedRequest[T]:
    """Parse JSON body into a Pydantic model with proper error handling.

    Args:
        request: The FastAPI request object.
        model_class: The Pydantic model class to parse into.

    Returns:
        ParsedRequest containing either the parsed model or an error response.
    """
    try:
        body = await request.json()
    except json.JSONDecodeError as e:
        return ParsedRequest(error=error_response(400, f"Bad Request: invalid JSON - {e.msg}"))

    try:
        model = model_class.model_validate(body)
        return ParsedRequest(model=model)
    except ValidationError as e:
        # Get the first error for a concise message
        first_error = e.errors()[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        msg = first_error["msg"]
        return ParsedRequest(
            error=error_response(400, f"Bad Request: validation error for '{field}' - {msg}")
        )


def is_json_content_type(request: Request) -> bool:
    """Check if the request has a JSON content type."""
    content_type = request.headers.get("content-type", "")
    return "application/json" in content_type
