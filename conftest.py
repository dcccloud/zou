import os
from pathlib import Path

import flask_bcrypt
import pytest

collect_ignore = ["plugins", "zou/plugin_template"]

# Must be set before zou.app is imported.
os.environ.setdefault("CACHE_TYPE", "simple")
os.environ.setdefault("BCRYPT_LOG_ROUNDS", "4")
os.environ.setdefault("DB_POOL_PRE_PING", "false")

_REAL_BCRYPT_FILES = {"test_auth_route.py", "test_auth_service.py"}

# flask_bcrypt module-level functions create a Bcrypt() instance without
# the app, so BCRYPT_LOG_ROUNDS is ignored and rounds default to 12.
# Wrap them to force 4 rounds in tests.
_TEST_ROUNDS = 4
_orig_generate = flask_bcrypt.generate_password_hash


def _fast_generate(password, rounds=None):
    return _orig_generate(password, rounds=rounds or _TEST_ROUNDS)


flask_bcrypt.generate_password_hash = _fast_generate


def _is_faas_only_test_session(config):
    args = getattr(config, "args", None) or []
    if not args:
        return False

    root_path = Path(str(config.rootpath))
    faas_path = (root_path / "tests" / "faas").resolve()
    checked_paths = []
    for arg in args:
        if arg.startswith("-"):
            continue
        path_arg = arg.split("::", 1)[0]
        path = Path(path_arg)
        if not path.is_absolute():
            path = root_path / path
        checked_paths.append(path)

    if not checked_paths:
        return False

    for path in checked_paths:
        try:
            path.resolve().relative_to(faas_path)
        except ValueError:
            return False
    return True


@pytest.fixture(autouse=True)
def _skip_bcrypt_check(request, monkeypatch):
    """Bypass bcrypt verification during login for non-auth tests."""
    if request.fspath.basename not in _REAL_BCRYPT_FILES:
        monkeypatch.setattr(
            "flask_bcrypt.check_password_hash",
            lambda *args, **kwargs: True,
        )


def pytest_configure(config):
    """Create database schema once for the entire test session."""
    if _is_faas_only_test_session(config):
        return

    from zou.app import app
    from zou.app.utils import dbhelpers

    # Register the admin blueprint so it can be tested.
    from zou.app.blueprints.admin import blueprint as admin_blueprint

    if "admin" not in app.blueprints:
        app.register_blueprint(admin_blueprint)

    with app.app_context():
        from zou.app import db

        dbhelpers.drop_all()
        db.engine.dispose()
        dbhelpers.create_all()
        db.engine.dispose()


def pytest_unconfigure(config):
    """Drop database schema at the end of the test session."""
    if _is_faas_only_test_session(config):
        return

    from zou.app import app
    from zou.app.utils import dbhelpers

    with app.app_context():
        dbhelpers.drop_all()
