"""Unit tests for app hooks configuration."""


def test_hooks_import():
    """Test that hooks module can be imported."""
    from flrts_extensions import hooks

    assert hooks is not None


def test_hooks_has_app_name():
    """Test that hooks defines app_name."""
    from flrts_extensions import hooks

    assert hasattr(hooks, "app_name")
    assert hooks.app_name == "flrts_extensions"


def test_hooks_has_app_title():
    """Test that hooks defines app_title."""
    from flrts_extensions import hooks

    assert hasattr(hooks, "app_title")
    assert hooks.app_title == "FLRTS Extensions"


def test_hooks_has_doc_events():
    """Test that hooks defines doc_events."""
    from flrts_extensions import hooks

    assert hasattr(hooks, "doc_events")
    assert isinstance(hooks.doc_events, dict)
