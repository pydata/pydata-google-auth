Changelog
=========

.. _changelog-1.8.0:

1.8.0 / (2023-05-09)
--------------------

- When running on Google Colab, try Colab-based authentication
  (``google.colab.auth.authenticate_user()``) before attempting the Google
  Application Default Credentials flow. (:issue:`68`)

.. _changelog-1.7.0:

1.7.0 / (2023-02-07)
--------------------

- Reissue of the library with the changes from 1.6.0 but with a new 
  version number due to a conflict in releases.

.. _changelog-1.6.0:

1.6.0 / (2023-02-07)
--------------------

- Adds decision logic to handle use cases where a user may not have the
  ability to log in via an Out of Band authentication flow. (:issue:`54`)

- Also provides an OAuth page as part of the documentation.

.. _changelog-1.5.0:

1.5.0 / (2023-01-09)
--------------------

- Adds ability to provide redirect uri. (:issue:`58`)

.. _changelog-1.4.0:

1.4.0 / (2022-03-14)
--------------------

- Default ``use_local_webserver`` to ``True``.  Google has deprecated the
  ``use_local_webserver = False`` `"out of band" (copy-paste) flow
  <https://developers.googleblog.com/2022/02/making-oauth-flows-safer.html?m=1#disallowed-oob>`_.
  The ``use_local_webserver = False`` option is planned to stop working in
  October 2022.

.. _changelog-1.3.0:

1.3.0 / (2021-12-03)
--------------------

- Adds support for Python 3.10. (:issue:`51`)
- Fixes typo in documentation. (:issue:`44`)

.. _changelog-1.2.0:

1.2.0 / (2021-04-21)
--------------------

- Adds :func:`pydata_google_auth.load_service_account_credentials` function to
  get service account credentials from the specified JSON path. (:issue:`39`)

.. _changelog-1.1.0:

1.1.0 / (2020-04-23)
--------------------

- Try a range of ports between 8080 and 8090 when ``use_local_webserver`` is
  ``True``. (:issue:`35`)

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
