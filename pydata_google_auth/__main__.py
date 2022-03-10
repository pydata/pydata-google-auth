"""Private module that implements a pydata-google-auth CLI tool."""

import argparse
import sys

from . import auth


LOGIN_HELP = (
    "Login to Google and save user credentials as a JSON file to use as "
    "Application Default Credentials."
)
LOGIN_SCOPES_DEFAULT = "https://www.googleapis.com/auth/cloud-platform"
LOGIN_SCOPES_HELP = (
    "Comma-separated list of scopes (permissions) to request from Google. "
    "See: https://developers.google.com/identity/protocols/googlescopes for "
    "a list of available scopes. Default: {}"
).format(LOGIN_SCOPES_DEFAULT)
LOGIN_CLIENT_ID_HELP_TEMPLATE = (
    "(Optional, but recommended) Client {}. Use this in combination with "
    "the {other} argument to authenticate with an application other than the "
    "default (PyData Auth). This argument is required to use APIs the track "
    "billing and quotas via the application (such as Cloud Vision), rather "
    "than billing the user (such as BigQuery does)."
)
LOGIN_CLIENT_ID_HELP = LOGIN_CLIENT_ID_HELP_TEMPLATE.format(
    "ID", other="--client-secret"
)
LOGIN_CLIENT_SECRET_HELP = LOGIN_CLIENT_ID_HELP_TEMPLATE.format(
    "secret", other="--client-id"
)
LOGIN_USE_LOCAL_WEBSERVER_HELP = (
    "Use a local webserver for the user authentication. This starts "
    "a webserver on localhost with a port between 8080 and 8089, "
    "inclusive, which allows the browser to pass a token directly to the "
    "program."
)

PRINT_TOKEN_HELP = "Load a credentials JSON file and print an access token."
PRINT_TOKEN_DESCRIPTION = r"""examples:

  Download the contents of gs://your-bucket/path/to/object.txt with the Google
  Cloud Storage JSON REST API.

    curl -X GET \
        -H "Authorization: Bearer $(python -m pydata_google_auth print-token credentials.json)" \
        "https://storage.googleapis.com/storage/v1/b/your-bucket/o/path%%2Fto%%2Fobject.txt?alt=media"
"""


def login(args):
    scopes = args.scopes.split(",")
    auth.save_user_credentials(
        scopes,
        args.destination,
        client_id=args.client_id,
        client_secret=args.client_secret,
        use_local_webserver=not args.nouse_local_webserver,
    )


def print_token(args):
    credentials = auth.load_user_credentials(args.credentials_path)
    print(credentials.token)


parser = argparse.ArgumentParser(
    prog="python -m pydata_google_auth",
    description="Manage credentials for Google APIs.",
)
subparsers = parser.add_subparsers(title="commands", dest="command")

login_parser = subparsers.add_parser("login", help=LOGIN_HELP)
login_parser.add_argument(
    "destination", help="Path of where to save user credentials JSON file."
)
login_parser.add_argument(
    "--scopes", help=LOGIN_SCOPES_HELP, default=LOGIN_SCOPES_DEFAULT
)
login_parser.add_argument("--client_id", help=LOGIN_CLIENT_ID_HELP)
login_parser.add_argument("--client_secret", help=LOGIN_CLIENT_SECRET_HELP)
login_parser.add_argument(
    "--use_local_webserver",
    action="store_true",
    help="Ignored. Defaults to true. To disable, set --nouse_local_webserver option.",
)
login_parser.add_argument(
    "--nouse_local_webserver", action="store_true", help=LOGIN_USE_LOCAL_WEBSERVER_HELP
)

print_token_parser = subparsers.add_parser(
    "print-token",
    help=PRINT_TOKEN_HELP,
    description=PRINT_TOKEN_DESCRIPTION,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
print_token_parser.add_argument(
    "credentials_path", help="Path of credentials JSON file."
)

args = parser.parse_args()
if args.command == "login":
    login(args)
elif args.command == "print-token":
    print_token(args)
else:
    print('Got unknown command "{}".'.format(args.command), file=sys.stderr)
    parser.print_help()
