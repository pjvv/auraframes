"""Custom exception classes for Aura Frames."""


class AuraError(Exception):
    """Base exception for Aura errors."""
    pass


class AuthenticationError(AuraError):
    """Raised when login fails."""
    pass


class APIError(AuraError):
    """Raised when API returns an error."""
    pass


class ConfigurationError(AuraError):
    """Raised when required configuration is missing."""
    pass


class ValidationError(AuraError):
    """Raised when input validation fails."""
    pass


class NetworkError(AuraError):
    """Raised when network requests fail."""
    pass
