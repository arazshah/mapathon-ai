class NeshanError(Exception):
    """Base exception for Neshan services."""


class NeshanAuthenticationError(NeshanError):
    """The Neshan API key is missing or invalid."""


class NeshanRateLimitError(NeshanError):
    """The Neshan API rate limit was exceeded."""


class NeshanNotFoundError(NeshanError):
    """The requested location or route was not found."""


class NeshanValidationError(NeshanError):
    """Neshan rejected request parameters."""


class NeshanServiceError(NeshanError):
    """Neshan service returned an unexpected error."""
