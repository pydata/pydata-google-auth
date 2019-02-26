Changelog
=========

.. _changelog-0.1.3:

0.1.3 / TBD
-----------

Bug Fixes
^^^^^^^^^

- Respect the ``dirname`` and ``filename`` arguments to the
  :class:`~pydata_google_auth.cache.ReadWriteCredentialsCache` and
  :class:`~pydata_google_auth.cache.WriteOnlyCredentialsCache` constructors.
  (:issue:`16`, :issue:`17`)

.. _changelog-0.1.2:

0.1.2 / (2019-02-01)
--------------------

Bug Fixes
^^^^^^^^^

- Don't write to the filesystem at module import time. This fixes an issue
  where the module could not be imported on systems where the file system is
  unwriteable. (:issue:`10`, :issue:`11`)

.. _changelog-0.1.1:

0.1.1 / (2018-10-26)
--------------------

- Add LICENSE.txt to package manifest.
- Document privacy policy.

.. _changelog-0.1.0:

0.1.0 / (2018-10-23)
--------------------

- Add ``cache`` module for configuring caching behaviors. (:issue:`1`)
- Fork the `pandas-gbq project <https://github.com/pydata/pandas-gbq>`_ and
  refactor out helpers for working with Google credentials.
