"""Test module for pydata_google_auth.cache"""

import errno
import json
import os
import os.path
import stat

import pytest

import google.oauth2.credentials

try:
    from importlib import reload

except ImportError:  # Py2 compat
    from six.moves import reload_module as reload


@pytest.fixture
def module_under_test():
    from pydata_google_auth import cache

    return cache


skip_on_windows = pytest.mark.skipif(
    os.name == "nt", reason="Windows doesn't use POSIX file modes."
)


@pytest.fixture
def umask(request):
    """Sets the umask, so that the default file modes are known."""
    previous_umask = os.umask(getattr(request, "param", 0o022))
    yield
    os.umask(previous_umask)


def _make_credentials(refresh_token="refresh_token"):
    return google.oauth2.credentials.Credentials(
        token="access_token",
        refresh_token=refresh_token,
        id_token="id_token",
        token_uri="token_uri",
        client_id="client_id",
        client_secret="client_secret",
        scopes=["scopes"],
    )


def _get_mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def _write_old_credentials(path, mode=0o644):
    path.write_text('{"refresh_token": "old_refresh_token"}')
    path.chmod(mode)


def _read_refresh_token(path):
    with open(path) as fp:
        return json.load(fp)["refresh_token"]


def test_import_unwriteable_fs(module_under_test, monkeypatch):
    """Test import with an unwritable filesystem.

    See: https://github.com/pydata/pydata-google-auth/issues/10
    """

    def raise_unwriteable(path):
        raise PermissionError()

    monkeypatch.setattr(os.path, "exists", lambda _: False)
    monkeypatch.setattr(os, "makedirs", raise_unwriteable)

    reload(module_under_test)

    assert module_under_test.NOOP is not None


def test__get_default_credentials_path_windows_wo_appdata(
    module_under_test, monkeypatch
):
    # Ensure default path returns something sensible on Windows, even if
    # APPDATA is not set. See:
    # https://github.com/pydata/pydata-google-auth/issues/29
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.delenv("APPDATA", raising=False)

    creds_path = module_under_test._get_default_credentials_path("dirname", "filename")
    assert creds_path is not None


def test__get_default_credentials_path_uses_xdg_config_home(
    module_under_test, monkeypatch
):
    """XDG_CONFIG_HOME should override the platform default config directory."""
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setenv("APPDATA", "/windows/config")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")

    creds_path = module_under_test._get_default_credentials_path("dirname", "filename")

    assert creds_path == os.path.join("/custom/config", "dirname", "filename")


def test__save_user_account_credentials_wo_directory(module_under_test, fs):
    """Directories should be created if they don't exist."""

    credentials = google.oauth2.credentials.Credentials(
        token="access_token",
        refresh_token="refresh_token",
        id_token="id_token",
        token_uri="token_uri",
        client_id="client_id",
        client_secret="client_secret",
        scopes=["scopes"],
    )
    path = "/home/username/.config/pydata/pydata_google_credentials.json"
    assert not os.path.exists("/home/username/.config/pydata/")

    module_under_test._save_user_account_credentials(credentials, path)

    with open(path) as fp:
        serialized_data = json.load(fp)
    assert serialized_data["refresh_token"] == "refresh_token"

    # Set the type so that the cached credentials file can be used as
    # application default credentials. See:
    # https://github.com/pydata/pydata-google-auth/issues/22
    assert serialized_data["type"] == "authorized_user"


@skip_on_windows
@pytest.mark.parametrize(
    "umask", [0o022, 0o000], ids=["umask_022", "umask_000"], indirect=True
)
def test__save_user_account_credentials_creates_private_file(
    module_under_test, tmp_path, umask
):
    """Only the user can access a new credentials file and its new directory."""
    path = tmp_path / "pydata" / "credentials.json"

    module_under_test._save_user_account_credentials(_make_credentials(), str(path))

    assert _get_mode(path) == 0o600
    assert _get_mode(path.parent) == 0o700


@skip_on_windows
def test__save_user_account_credentials_keeps_existing_directory_mode(
    module_under_test, tmp_path, umask
):
    """The permissions of a directory that already exists don't change."""
    tmp_path.chmod(0o755)
    path = tmp_path / "credentials.json"

    module_under_test._save_user_account_credentials(_make_credentials(), str(path))

    assert _get_mode(tmp_path) == 0o755
    assert _get_mode(path) == 0o600


@skip_on_windows
def test__save_user_account_credentials_replaces_readable_file(
    module_under_test, tmp_path, umask
):
    """New credentials never go into a file that other users can read.

    A process that opened the old file still sees only the old credentials.
    """
    path = tmp_path / "credentials.json"
    _write_old_credentials(path, mode=0o644)

    with open(path) as old_file:
        module_under_test._save_user_account_credentials(
            _make_credentials("new_refresh_token"), str(path)
        )
        assert "new_refresh_token" not in old_file.read()

    assert _get_mode(path) == 0o600
    assert _read_refresh_token(path) == "new_refresh_token"


@skip_on_windows
def test__save_user_account_credentials_writes_through_symlink(
    module_under_test, tmp_path, umask
):
    """A symbolic link is kept, and the file it points to is updated."""
    target = tmp_path / "target.json"
    _write_old_credentials(target, mode=0o644)
    link = tmp_path / "credentials.json"
    link.symlink_to(target)

    module_under_test._save_user_account_credentials(
        _make_credentials("new_refresh_token"), str(link)
    )

    assert link.is_symlink()
    assert _get_mode(target) == 0o600
    assert _read_refresh_token(target) == "new_refresh_token"


@skip_on_windows
def test__save_user_account_credentials_writes_in_place_if_replace_fails(
    module_under_test, tmp_path, monkeypatch, umask
):
    """A file that can't be replaced, such as a mount point, is rewritten."""
    path = tmp_path / "credentials.json"
    _write_old_credentials(path, mode=0o644)

    def raise_busy(src, dst):
        raise OSError(errno.EBUSY, os.strerror(errno.EBUSY))

    monkeypatch.setattr(os, "replace", raise_busy)

    module_under_test._save_user_account_credentials(
        _make_credentials("new_refresh_token"), str(path)
    )

    assert _get_mode(path) == 0o600
    assert _read_refresh_token(path) == "new_refresh_token"
    assert os.listdir(tmp_path) == ["credentials.json"]


def test__save_user_account_credentials_keeps_file_if_write_fails(
    module_under_test, tmp_path, monkeypatch
):
    """If the new credentials can't be written, the old file is unchanged."""
    path = tmp_path / "credentials.json"
    _write_old_credentials(path)

    class DiskFullFile(object):
        def __init__(self, fd):
            os.close(fd)

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def write(self, data):
            raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    monkeypatch.setattr(os, "fdopen", lambda fd, *args, **kwargs: DiskFullFile(fd))

    module_under_test._save_user_account_credentials(
        _make_credentials("new_refresh_token"), str(path)
    )

    assert _read_refresh_token(path) == "old_refresh_token"
    assert os.listdir(tmp_path) == ["credentials.json"]


def test__save_user_account_credentials_bare_filename(
    module_under_test, tmp_path, monkeypatch, umask
):
    """A filename without a directory is saved in the current directory."""
    monkeypatch.chdir(tmp_path)

    module_under_test._save_user_account_credentials(
        _make_credentials(), "credentials.json"
    )

    path = tmp_path / "credentials.json"
    assert _read_refresh_token(path) == "refresh_token"
    if os.name != "nt":
        assert _get_mode(path) == 0o600


@skip_on_windows
@pytest.mark.parametrize("use_symlink", [False, True], ids=["file", "symlink"])
def test__save_user_account_credentials_refuses_other_users_file(
    module_under_test, tmp_path, monkeypatch, umask, use_symlink
):
    """Credentials are never written to a file that another user owns."""
    target = tmp_path / "other_user.json"
    _write_old_credentials(target, mode=0o666)
    path = target
    if use_symlink:
        path = tmp_path / "credentials.json"
        path.symlink_to(target)
    # Act as a user who doesn't own the file.
    monkeypatch.setattr(os, "geteuid", lambda: target.stat().st_uid + 1)

    module_under_test._save_user_account_credentials(
        _make_credentials("new_refresh_token"), str(path)
    )

    assert _read_refresh_token(target) == "old_refresh_token"
    assert _get_mode(target) == 0o666


@skip_on_windows
@pytest.mark.parametrize("is_owner", [True, False], ids=["own", "other_users"])
def test__save_user_account_credentials_writes_only_to_own_pipe(
    module_under_test, tmp_path, monkeypatch, is_owner
):
    """Credentials go to a named pipe only if the user owns it."""
    pipe = tmp_path / "credentials.json"
    os.mkfifo(pipe)
    reader = os.open(pipe, os.O_RDONLY | os.O_NONBLOCK)
    try:
        if not is_owner:
            # Act as a user who doesn't own the pipe.
            monkeypatch.setattr(os, "geteuid", lambda: pipe.stat().st_uid + 1)

        module_under_test._save_user_account_credentials(_make_credentials(), str(pipe))

        written = os.read(reader, 4096)
    finally:
        os.close(reader)

    if is_owner:
        assert b"refresh_token" in written
    else:
        assert written == b""


@skip_on_windows
def test__save_user_account_credentials_root_keeps_owner(
    module_under_test, tmp_path, monkeypatch, umask
):
    """Root, such as in a container, rewrites another user's file in place."""
    path = tmp_path / "credentials.json"
    _write_old_credentials(path, mode=0o644)
    inode = path.stat().st_ino
    monkeypatch.setattr(os, "geteuid", lambda: 0)

    module_under_test._save_user_account_credentials(
        _make_credentials("new_refresh_token"), str(path)
    )

    assert path.stat().st_ino == inode
    assert _get_mode(path) == 0o600
    assert _read_refresh_token(path) == "new_refresh_token"


@skip_on_windows
def test_ReadWriteCredentialsCache_load_removes_other_users_access(
    module_under_test, tmp_path, monkeypatch
):
    """Loading restricts a credentials file that an earlier version saved."""
    path = tmp_path / "credentials.json"
    _write_old_credentials(path, mode=0o644)
    monkeypatch.setattr(
        module_under_test,
        "_load_user_credentials_from_file",
        lambda credentials_path: "loaded credentials",
    )
    cache = module_under_test.ReadWriteCredentialsCache()
    cache._path = str(path)

    assert cache.load() == "loaded credentials"
    assert _get_mode(path) == 0o600


@skip_on_windows
def test_ReadWriteCredentialsCache_load_keeps_directory_mode(
    module_under_test, tmp_path, monkeypatch
):
    """Loading doesn't change the permissions of anything but a file."""
    tmp_path.chmod(0o755)
    monkeypatch.setattr(
        module_under_test,
        "_load_user_credentials_from_file",
        lambda credentials_path: None,
    )
    cache = module_under_test.ReadWriteCredentialsCache()
    cache._path = str(tmp_path)

    assert cache.load() is None
    assert _get_mode(tmp_path) == 0o755


def test_ReadWriteCredentialsCache_load_wo_file(module_under_test, tmp_path):
    """Loading returns None when there is no credentials file yet."""
    cache = module_under_test.ReadWriteCredentialsCache()
    cache._path = str(tmp_path / "pydata" / "credentials.json")

    assert cache.load() is None
    assert not (tmp_path / "pydata").exists()


def test_ReadWriteCredentialsCache_sets_path(module_under_test):
    """ReadWriteCredentialsCache ctor should respect dirname and filename.

    See: https://github.com/pydata/pydata-google-auth/issues/16
    """
    cache = module_under_test.ReadWriteCredentialsCache(
        dirname="dirtest", filename="filetest.json"
    )
    path = os.path.normpath(cache._path)
    parts = path.split(os.sep)
    assert parts[-2] == "dirtest"
    assert parts[-1] == "filetest.json"


def test_WriteOnlyCredentialsCache_sets_path(module_under_test):
    """ReadWriteCredentialsCache ctor should respect dirname and filename.

    See: https://github.com/pydata/pydata-google-auth/issues/16
    """
    cache = module_under_test.WriteOnlyCredentialsCache(
        dirname="dirtest", filename="filetest.json"
    )
    path = os.path.normpath(cache._path)
    parts = path.split(os.sep)
    assert parts[-2] == "dirtest"
    assert parts[-1] == "filetest.json"
