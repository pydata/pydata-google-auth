Introduction
============

pydata-google-auth wraps the `google-auth
<https://google-auth.readthedocs.io/>`_ and `google-auth-oauthlib
<https://google-auth-oauthlib.readthedocs.io/>`_ libraries to make it easier
to get and cache user credentials for accessing the Google APIs from
locally-installed data tools and libraries.

See the `Google Cloud Platform authentication guide
<https://cloud.google.com/docs/authentication/>`_ for best practices on
authentication in production server contexts.

User credentials
----------------

Use the :func:`pydata_google_auth.get_user_credentials` to get user
credentials, authenticated to Google APIs.

Default credentials
-------------------

Data library and tool authors can use the :func:`pydata_google_auth.default`
function to get `Application Default Credentials
<https://google-auth.readthedocs.io/en/latest/reference/google.auth.html#google.auth.default>`_
and fallback to user credentials when no valid Application Default
Credentials are found.

When wrapping the :func:`pydata_google_auth.default` method for use in your
tool or library, please provide your own client ID and client secret. Enable
the APIs your users will need in the project which owns the client ID and
secrets. Note that some APIs, such as Cloud Vision, bill the *client*
project. Verify that the API you are enabling bills the user's project not
the client project.
