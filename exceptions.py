from __future__ import annotations


class DidaError(Exception):
    """Base exception for the Dida365 plugin."""


class DidaConfigurationError(DidaError):
    """Raised when required plugin configuration is missing."""


class DidaNetworkError(DidaError):
    """Raised when the plugin cannot reach the Dida365 API."""


class DidaApiError(DidaError):
    """Raised when the Dida365 API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        payload: str = "",
    ) -> None:
        """Initialize the API error.

        Args:
            message: Human-readable error description.
            status: Optional HTTP status code from the API response.
            payload: Optional raw response body (truncated to 500
                characters) for debugging.
        """
        super().__init__(message)
        self.status = status
        self.payload = payload


class DidaAuthenticationError(DidaApiError):
    """Raised when the Dida365 API rejects the provided credentials."""


class DidaNotFoundError(DidaApiError):
    """Raised when a requested resource does not exist."""


class DidaValidationError(DidaError):
    """Raised when plugin-side validation fails."""
