pydata-google-auth
==================

|Build Status| |Version Status| |Coverage Status|

**pydata-google-auth** is a package providing helpers for authenticating to Google APIs.


Installation
------------


Install latest release version via conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   $ conda install pydata-google-auth --channel conda-forge

Install latest release version via pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   $ pip install pydata-google-auth

Install latest development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    $ pip install git+https://github.com/pydata/pydata-google-auth.git


Usage
-----

Use the ``pydata_google_auth.get_user_credentials()`` function to
authenticate to Google APIs with user credentials.

.. code-block:: python

    import pydata_google_auth
    credentials = pydata_google_auth.get_user_credentials(
        ['https://www.googleapis.com/auth/cloud-platform'],
    )

    # Use the credentials in other libraries, such as the Google BigQuery
    # client library.
    from google.cloud import bigquery
    client = bigquery.Client(project='YOUR-PROJECT-ID', credentials=credentials)

See the `pydata-google-auth documentation <https://pydata-google-auth.readthedocs.io/>`_ for more details.

.. |Build Status| image:: https://circleci.com/gh/pydata/pydata-google-auth/tree/master.svg?style=svg
   :target: https://circleci.com/gh/pydata/pydata-google-auth/tree/master
.. |Version Status| image:: https://img.shields.io/pypi/v/pydata-google-auth.svg
   :target: https://pypi.python.org/pypi/pydata-google-auth/
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/pydata/pydata-google-auth.svg
   :target: https://codecov.io/gh/pydata/pydata-google-auth/
