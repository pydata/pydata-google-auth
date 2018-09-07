
from .auth import default
from .auth import get_user_credentials
from ._version import get_versions

versions = get_versions()
__version__ = versions.get('closest-tag', versions['version'])
__git_revision__ = versions['full-revisionid']

"""Google BigQuery API wrapper.
The main concepts with this API are:
- :class:`~google.cloud.bigquery.client.Client` manages connections to the
  BigQuery API. Use the client methods to run jobs (such as a
  :class:`~google.cloud.bigquery.job.QueryJob` via
  :meth:`~google.cloud.bigquery.client.Client.query`) and manage resources.
- :class:`~google.cloud.bigquery.dataset.Dataset` represents a
  collection of tables.
- :class:`~google.cloud.bigquery.table.Table` represents a single "relation".
"""

__all__ = [
    '__version__',
    '__git_revision__',
    'default',
    'get_user_credentials',
]
