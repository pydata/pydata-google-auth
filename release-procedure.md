# Releasing pydata-google-auth

*   Update the CHANGELOG. Example: https://github.com/pydata/pydata-google-auth/pull/60

*   Tag commit

        git tag -a x.x.x -m 'Version x.x.x'

*   and push to github

        git push upstream main --tags

*   Build the package

        git clean -xfd
        python setup.py sdist bdist_wheel --universal

*   Upload to test PyPI

        twine upload --repository testpypi dist/*

*   Try out test PyPI package

        pip install --upgrade --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pydata-google-auth

*   Upload to PyPI

        twine upload dist/*

*   Do a pull-request to the feedstock on `pydata-google-auth-feedstock <https://github.com/conda-forge/pydata-google-auth-feedstock/>`__

        update the version
        update the SHA256 (retrieve from PyPI)
