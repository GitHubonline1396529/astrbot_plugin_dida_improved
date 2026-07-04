from __future__ import annotations

from astrbot_plugin_dida_improved.exceptions import (
    DidaApiError,
    DidaAuthenticationError,
    DidaConfigurationError,
    DidaError,
    DidaNetworkError,
    DidaNotFoundError,
    DidaValidationError,
)


class TestExceptionHierarchy:
    def test_dida_error_is_base(self):
        assert issubclass(DidaConfigurationError, DidaError)
        assert issubclass(DidaNetworkError, DidaError)
        assert issubclass(DidaApiError, DidaError)
        assert issubclass(DidaValidationError, DidaError)

    def test_auth_and_not_found_inherit_api_error(self):
        assert issubclass(DidaAuthenticationError, DidaApiError)
        assert issubclass(DidaNotFoundError, DidaApiError)

    def test_dida_error_str(self):
        exc = DidaError("test")
        assert str(exc) == "test"

    def test_api_error_with_status_and_payload(self):
        exc = DidaApiError("API error", status=400, payload="bad request")
        assert str(exc) == "API error"
        assert exc.status == 400
        assert exc.payload == "bad request"

    def test_api_error_defaults(self):
        exc = DidaApiError("err")
        assert exc.status is None
        assert exc.payload == ""

    def test_configuration_error_str(self):
        exc = DidaConfigurationError("missing token")
        assert str(exc) == "missing token"

    def test_network_error_str(self):
        exc = DidaNetworkError("connection refused")
        assert str(exc) == "connection refused"

    def test_validation_error_str(self):
        exc = DidaValidationError("invalid input")
        assert str(exc) == "invalid input"
