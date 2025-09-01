from server import sanitize_relative_path


def test_sanitize_relative_path_removes_forbidden_chars():
    """Path components are cleaned and traversal removed."""
    path = '../weird\\path?name.txt'
    expected = 'weird/pathname.txt'
    assert sanitize_relative_path(path) == expected
