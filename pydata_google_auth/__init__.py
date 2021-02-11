from .auth import default
from .auth import get_user_credentials
from .auth import load_user_credentials
from .auth import save_user_credentials
from .auth import load_service_account_credentials
from ._version import get_versions

versions = get_versions()
__version__ = versions.get("closest-tag", versions["version"])
__git_revision__ = versions["full-revisionid"]

"""pydata-google-auth

This package provides helpers for fetching Google API credentials.
"""

__all__ = [
    "__version__",
    "__git_revision__",
    "default",
    "get_user_credentials",
    "load_user_credentials",
    "save_user_credentials",
    "load_service_account_credentials",
]
