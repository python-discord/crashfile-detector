import typing as t
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import BaseModel, validator

ALLOWED_SCHEMES = (
    "http",
    "https"
)


class ErrorMessages(t.NamedTuple):
    """Variour errors that can be raised while processing a request."""

    NO_CONTENT_HEADER = "Remote server didn't return a Content-Length header."
    NON_INT_CONTENT_HEADER = "Remote server returned a non-integer Content-Length header."
    CONTENT_TOO_BIG = "The remote file was too big to download."
    INVALID_URL = "URL must be a valid url!"


class Pong(BaseModel):
    """A response to the ping endpoint."""

    message: str = "Pong!"


class SuspectUrl(BaseModel):
    """The string to be checked for crash potential."""

    url: str

    @validator("url")
    def url_must_be_valid_url(cls, url: str) -> str:
        """Ensure that the url is a valid url."""
        result = urlparse(url)
        if not all([result.scheme in ALLOWED_SCHEMES, result.netloc, result.path]):
            raise HTTPException(status_code=413, detail=ErrorMessages.INVALID_URL)
        return url


class Dimensions(BaseModel):
    """The dimensions of the passed file."""

    width: int
    height: int


class FileInfo(BaseModel):
    """Information about the passed file."""

    safe: bool
    scanned_count: int
    dimensions: Dimensions
    format: str
