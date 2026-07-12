"""Domain-level custom exceptions for Ledgerly."""


class UserAlreadyExists(Exception):
    """Raised when creating a user that already exists."""


class UserNotFound(Exception):
    """Raised when a user cannot be found."""


class TransactionNotFound(Exception):
    """Raised when a transaction cannot be found."""


class InvalidTransaction(Exception):
    """Raised when a transaction payload fails business validation."""
