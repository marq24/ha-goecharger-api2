"""Bridge: constructor validation and error handling of the HTTP write."""
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.goecharger_api2.pygoecharger_ha import GoeChargerApiV2Bridge


def test_constructor_needs_host_or_serial_and_token():
    with pytest.raises(ValueError, match="host, or a serial"):
        GoeChargerApiV2Bridge(web_session=None, intg_type="charger")


class _Response:
    def __init__(self, status, content_length, json_body=None):
        self.status = status
        self.content_length = content_length
        self.headers = {} if content_length is None else {"Content-Length": str(content_length)}
        self.json = AsyncMock(return_value=json_body)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _bridge(response):
    session = SimpleNamespace(get=lambda *args, **kwargs: response)
    return GoeChargerApiV2Bridge(web_session=session, intg_type="charger", host="192.0.2.10")


async def test_error_response_with_body_is_returned():
    bridge = _bridge(_Response(500, content_length=20, json_body={"amp": "error"}))
    assert await bridge._write_values_int({"amp": "16"}, "amp", 16) == {"err": {"amp": "error"}}


async def test_error_response_without_content_length_does_not_raise_keyerror(caplog):
    """Chunked responses have no Content-Length header: this used to raise a KeyError."""
    bridge = _bridge(_Response(500, content_length=None))
    with caplog.at_level(logging.WARNING):
        assert await bridge._write_values_int({"amp": "16"}, "amp", 16) == {}
    assert "KeyError" not in caplog.text
