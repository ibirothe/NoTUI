class NoTUIError(Exception):
    """Base application exception."""


class DatabaseOpenError(NoTUIError):
    """Raised when the SQLite database cannot be opened."""


class MigrationError(NoTUIError):
    """Raised when a database migration fails."""


class TodoNotFoundError(NoTUIError):
    """Raised when a note cannot be found."""


class ValidationError(NoTUIError):
    """Raised when user data fails validation."""


class ConfigError(NoTUIError):
    """Raised when configuration is invalid."""
