Changelog
=========

.. _changelog-1.0.0:

1.0.0 / (2020-04-20)
--------------------

- Mark package as 1.0, generally available.
- Update introduction with link to instructions on creating a Google Cloud
  project. (:issue:`18`)

.. _changelog-0.3.0:

0.3.0 / (2020-02-04)
--------------------

- Add ``python -m pydata_google_auth`` CLI for working with user credentials.
  (:issue:`28`)

.. _changelog-0.2.1:

0.2.1 / (2019-12-12)
--------------------

- Re-enable ``auth_local_webserver`` in ``default`` method. Show warning,
  rather than fallback to console.

.. _changelog-0.2.0:

0.2.0 / (2019-12-12)
--------------------

- **Deprecate** ``auth_local_webserver`` argument in favor of
  ``use_local_webserver`` argument (:issue:`20`).

New Features
^^^^^^^^^^^^^

- Adds :func:`pydata_google_auth.save_user_credentials` function to get user
  credentials and then save them to a specified JSON path. (:issue:`22`)

Bug Fixes
^^^^^^^^^

- Update OAuth2 token endpoint to latest URI from Google. (:issue:`27`)
- Don't raise error when the ``APPDATA`` environment variable isn't set on
  Windows. (:issue:`29`)

.. _changelog-0.1.3:

0.1.3 / (2019-02-26)
--------------------

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
