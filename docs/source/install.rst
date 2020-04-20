Installation
============

You can install pydata-google-auth with ``conda``, ``pip``, or by installing from source.

Conda
-----

.. code-block:: shell

   $ conda install pydata-google-auth --channel conda-forge

This installs pydata-google-auth and all common dependencies, including ``google-auth``.

Pip
---

To install the latest version of pydata-google-auth: from the

.. code-block:: shell

    $ pip install pydata-google-auth -U

This installs pydata-google-auth and all common dependencies, including ``google-auth``.


Install from Source
-------------------

.. code-block:: shell

    $ pip install git+https://github.com/pydata/pydata-google-auth.git


Dependencies
------------

This module requires following additional dependencies:

- `google-auth <https://github.com/googleapis/google-auth-library-python>`__: authentication and authorization for Google's API
- `google-auth-oauthlib <https://github.com/googleapis/google-auth-library-python-oauthlib>`__: integration with `oauthlib <https://github.com/idan/oauthlib>`__ for end-user authentication
