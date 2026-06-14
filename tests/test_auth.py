from pathlib import Path

import app


def test_app_has_no_password_gate():
    source = Path("app.py").read_text()

    assert not hasattr(app, "require_login")
    assert not hasattr(app, "is_authenticated")
    assert "APP_PASSWORD" not in source
    assert "Private access" not in source
