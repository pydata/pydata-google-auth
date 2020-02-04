Command-line Reference
======================

Run the ``pydata_google_auth`` CLI with ``python -m pydata_google_auth``.

.. code:: bash

   usage: python -m pydata_google_auth [-h] {login,print-token} ...

   Manage credentials for Google APIs.

   optional arguments:
     -h, --help           show this help message and exit

   commands:
     {login,print-token}
       login              Login to Google and save user credentials as a JSON
                          file to use as Application Default Credentials.
       print-token        Load a credentials JSON file and print an access token.


Saving user credentials with ``login``
--------------------------------------

.. code:: bash

   usage: python -m pydata_google_auth login [-h] [--scopes SCOPES]
                                             [--client_id CLIENT_ID]
                                             [--client_secret CLIENT_SECRET]
                                             [--use_local_webserver]
                                             destination

   positional arguments:
     destination           Path of where to save user credentials JSON file.

   optional arguments:
     -h, --help            show this help message and exit
     --scopes SCOPES       Comma-separated list of scopes (permissions) to
                           request from Google. See: https://developers.google.co
                           m/identity/protocols/googlescopes for a list of
                           available scopes. Default:
                           https://www.googleapis.com/auth/cloud-platform
     --client_id CLIENT_ID
                           (Optional, but recommended) Client ID. Use this in
                           combination with the --client-secret argument to
                           authenticate with an application other than the
                           default (PyData Auth). This argument is required to
                           use APIs the track billing and quotas via the
                           application (such as Cloud Vision), rather than
                           billing the user (such as BigQuery does).
     --client_secret CLIENT_SECRET
                           (Optional, but recommended) Client secret. Use this in
                           combination with the --client-id argument to
                           authenticate with an application other than the
                           default (PyData Auth). This argument is required to
                           use APIs the track billing and quotas via the
                           application (such as Cloud Vision), rather than
                           billing the user (such as BigQuery does).
     --use_local_webserver
                           Use a local webserver for the user authentication.
                           This starts a webserver on localhost, which allows the
                           browser to pass a token directly to the program.

Save credentials with Cloud Platform scope to ``~/keys/google-credentials.json``.

.. code:: bash

   python -m pydata_google_auth login ~/keys/google-credentials.json

Loading user credentials with ``print-token``
---------------------------------------------

Print an access token associate with the credentials at
``~/keys/google-credentials.json``.

.. code:: bash

   python -m pydata_google_auth print-token ~/keys/google-credentials.json

Use ``curl`` and the ``credentials.json`` user credentials file to download
the contents of ``gs://your-bucket/path/to/object.txt`` with the Google Cloud
Storage JSON REST API.

.. code:: bash

   curl -X GET \
       -H "Authorization: Bearer $(python -m pydata_google_auth print-token credentials.json)" \
       "https://storage.googleapis.com/storage/v1/b/your-bucket/o/path%%2Fto%%2Fobject.txt?alt=media"
