from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str

    class Config:
        json_schema_extra = {
            "example": {"detail": "An error occurred"},
        }


# ── Reusable OpenAPI response definitions ──────────────────────────────


def _error(status: int, description: str, example_detail: str) -> dict:
    """Build a single OpenAPI `responses` entry."""
    return {
        status: {
            "description": description,
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": example_detail},
                }
            },
        }
    }


# Individual response helpers
UNAUTHORIZED_401 = _error(
    401,
    "Unauthorized – Missing or invalid authentication token.",
    "Could not validate credentials",
)

FORBIDDEN_403 = _error(
    403,
    "Forbidden – You do not have permission to perform this action.",
    "Access denied",
)

NOT_FOUND_404 = _error(
    404,
    "Not Found – The requested resource does not exist.",
    "Resource not found",
)

BAD_REQUEST_400 = _error(
    400,
    "Bad Request – The request could not be processed.",
    "Invalid request",
)

VALIDATION_422 = _error(
    422,
    "Validation Error – One or more fields failed validation.",
    "Request body or parameters failed validation",
)

INTERNAL_SERVER_ERROR_500 = _error(
    500,
    "Internal Server Error – An unexpected error occurred on the server.",
    "An unexpected error occurred. Please try again later.",
)


# ── Convenience combinators ─────────────────────────────────────────────


def build_responses(*dicts: dict) -> dict:
    """Merge multiple single-key response dicts into one ``responses`` mapping."""
    merged: dict = {}
    for d in dicts:
        merged.update(d)
    return merged


# Pre-built combos used across many routes
AUTHENTICATED_RESPONSES = build_responses(
    UNAUTHORIZED_401, VALIDATION_422, INTERNAL_SERVER_ERROR_500
)

AUTHENTICATED_FORBIDDEN_RESPONSES = build_responses(
    UNAUTHORIZED_401, FORBIDDEN_403, VALIDATION_422, INTERNAL_SERVER_ERROR_500
)

AUTHENTICATED_NOT_FOUND_RESPONSES = build_responses(
    UNAUTHORIZED_401, NOT_FOUND_404, VALIDATION_422, INTERNAL_SERVER_ERROR_500
)

AUTHENTICATED_FORBIDDEN_NOT_FOUND_RESPONSES = build_responses(
    UNAUTHORIZED_401, FORBIDDEN_403, NOT_FOUND_404, VALIDATION_422, INTERNAL_SERVER_ERROR_500
)

AUTHENTICATED_BAD_REQUEST_NOT_FOUND_RESPONSES = build_responses(
    UNAUTHORIZED_401, BAD_REQUEST_400, NOT_FOUND_404, VALIDATION_422, INTERNAL_SERVER_ERROR_500
)

AUTHENTICATED_ALL_RESPONSES = build_responses(
    UNAUTHORIZED_401, FORBIDDEN_403, BAD_REQUEST_400, NOT_FOUND_404,
    VALIDATION_422, INTERNAL_SERVER_ERROR_500,
)
