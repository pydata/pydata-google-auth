class PyDataCredentialsError(ValueError):
    """
    Raised when invalid credentials are provided, or tokens have expired.
    """


class PyDataConnectionError(RuntimeError):
    """
    Raised when unable to fetch credentials due to connection error.
    """
