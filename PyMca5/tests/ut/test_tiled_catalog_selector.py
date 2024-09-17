import enable_pymca_import  # noqa: F401

import logging
from contextlib import nullcontext as does_not_raise
from typing import Any, Mapping, Sequence
from unittest.mock import Mock, patch

import pytest

from PyMca5.PyMcaGui.io.TiledCatalogSelector import (
    TiledCatalogSelector, validate_url_scheme, validate_url_syntax,
)


@pytest.mark.parametrize(
    "optional_args",
    (
        {},
        {"url": "test"},
        {"validators": {"url": [validate_url_syntax, validate_url_scheme]}}
    )
)
def test_init(optional_args: Mapping[str, Any]):
    """Can create a TiledCatalogSelector object."""
    TiledCatalogSelector()


def test_on_url_focus_in_event():
    """Event handler creates a string buffer for a new url without changing the existing url."""
    expected_url = "before"
    model = TiledCatalogSelector(url=expected_url)
    event = Mock()

    assert model.url == expected_url

    model.url_buffer = "Pre-existing content"
    model.on_url_focus_in_event(event)

    assert model.url_buffer is None
    assert model.url == expected_url


def test_clearurl_buffer():
    """FocusIn event clears the string buffer for a new url."""
    buffer_name = "url_buffer"
    model = TiledCatalogSelector()
    event = Mock()
    setattr(model, buffer_name, "Previously edited URL")

    buffer_text = getattr(model, buffer_name)
    assert len(buffer_text) > 0

    model.on_url_focus_in_event(event)
    assert getattr(model, buffer_name) is None


def test_on_url_text_edited():
    """Event handler replaces the url buffer without changing the existing url."""
    expected_url = "before"
    buffer_name = "url_buffer"
    model = TiledCatalogSelector(url=expected_url)
    setattr(model, buffer_name, "")

    assert model.url == expected_url
    assert getattr(model, buffer_name) == ""

    expected_text = "Update #1"
    model.on_url_text_edited(expected_text)
    assert getattr(model, buffer_name) == expected_text

    expected_text = "Update #2"
    model.on_url_text_edited(expected_text)
    assert getattr(model, buffer_name) == expected_text

    assert model.url == expected_url


def test_on_url_editing_finished():
    """Event handler replaces the existing url with the contents of the buffer."""
    expected_url = "after"
    buffer_name = "url_buffer"
    model = TiledCatalogSelector(url="before")
    setattr(model, buffer_name, expected_url)

    model.on_url_editing_finished()
    assert model.url == expected_url
    assert getattr(model, buffer_name) is None


def test_on_connect_clicked():
    """Event handler updates client with connection to the url, emits Qt signal."""
    expected_url = "URL is not used here"
    expected_api_url = "API URL is not used here"
    model = TiledCatalogSelector(url=expected_url)

    with patch.object(model, "client_from_url") as mock_client_constructor:
        client = Mock()
        client.uri = model.url
        client.context.api_uri = expected_api_url
        mock_client_constructor.return_value = client

        with patch.object(model, "client_connected") as mock_signal:
            mock_signal.emit = Mock()
            model.on_connect_clicked()

    assert model.client.uri == expected_url
    mock_signal.emit.assert_called_once_with(expected_url, expected_api_url)


def test_on_connect_exception(caplog: pytest.LogCaptureFixture):
    """Event handler logs a connection error and does not disrupt an existing connection."""
    caplog.set_level(logging.INFO)
    client = Mock()
    model = TiledCatalogSelector(client=client)
    expected_message = "Mock connection error"

    with patch.object(model, "client_from_url") as mock_client_constructor:
        mock_client_constructor.side_effect = Exception(expected_message)
        model.on_connect_clicked()

    assert expected_message in caplog.messages
    assert model.client is client


@pytest.mark.parametrize(
    "url, expected_context",
    (
        # Valid URLs
        ("https://tiled.example.com", does_not_raise()),
        ("https://tiled.example.com:8000", does_not_raise()),
        ("https://tiled.example.com/api/v1/metadata", does_not_raise()),
        ("https://tiled.example.com/api/v1/array/block/test?block=1", does_not_raise()),
        # Invalid URLs
        ("https.tiled.example.com", pytest.raises(ValueError)),
        ("https:/tiled.example.com", pytest.raises(ValueError)),
        ("Not a URL", pytest.raises(ValueError)),
    )
)
def test_syntax_validator(url: str, expected_context):
    """Validate the syntax of the URL."""
    with expected_context:
        validate_url_syntax(url)


@pytest.mark.parametrize(
    "url, expected_context, valid_schemes",
    (
        # Valid URL schemes
        ("https://tiled.example.com", does_not_raise(), None),
        ("http://tiled.example.com", does_not_raise(), None),
        ("tiled://tiled.example.com", does_not_raise(), ("https", "tiled")),
        # Invalid URL schemes
        ("ftp://tiled.example.com", pytest.raises(ValueError), None),
        ("tiled://tiled.example.com", pytest.raises(ValueError), None),
        ("http://tiled.example.com", pytest.raises(ValueError), ("https",)),
    )
)
def test_scheme_validator(url: str, expected_context, valid_schemes: Sequence[str]):
    """Validate the scheme of the URL against valid_schemes."""
    kwargs = {"valid_schemes": valid_schemes} if valid_schemes else {}
    with expected_context:
        validate_url_scheme(url, **kwargs)


@pytest.mark.parametrize(
    "url, expected_url",
    (
        # Valid URL scheme
        ("https://tiled.example.com", "https://tiled.example.com"),
        # Invalid URL
        ("after", "before"),
    )
)
def test_validation_on_url_editing_finished(
    url: str,
    expected_url: str,
    caplog: pytest.LogCaptureFixture,
):
    """Event handler replaces the existing url if validator succeeds."""
    caplog.set_level(logging.INFO)
    validators = {"url": [validate_url_scheme]}
    model = TiledCatalogSelector(url="before", validators=validators)
    model.url_buffer = url

    model.on_url_editing_finished()
    assert model.url == expected_url

    if model.url == "before":
        # URL was not updated because its scheme was not valid
        assert " is not a valid URL." in caplog.text
        assert "URL must include a scheme." in caplog.text
