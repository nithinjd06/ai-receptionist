"""
Request ID and unique identifier generation.
"""
import uuid
from contextvars import ContextVar

# Context variable to store request ID across async calls
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    request_id_ctx.set(request_id)


def get_request_id() -> str:
    """Get the request ID from the current context."""
    return request_id_ctx.get()







