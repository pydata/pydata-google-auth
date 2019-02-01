To build a local copy of the pydata-google-auth docs, install the programs in
requirements-docs.txt and run 'make html'. If you use the conda package manager
these commands suffice::

  git clone git@github.com:pydata/pydata-google-auth.git
  cd pydata-google-docs/docs/source
  conda create -n pydata-google-auth-docs --file ../requirements-docs.txt
  source activate pydata-google-auth-docs
  make html
  open _build/html/index.html
