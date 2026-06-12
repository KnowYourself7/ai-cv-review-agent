from app import is_authenticated


def test_is_authenticated_allows_local_dev_when_no_password_is_configured():
    assert is_authenticated("", "", False)


def test_is_authenticated_requires_matching_password_when_configured():
    assert is_authenticated("secret", "secret", False)
    assert not is_authenticated("wrong", "secret", False)


def test_is_authenticated_keeps_existing_session_login():
    assert is_authenticated("", "secret", True)
