import pytest
from pydantic import BaseModel

from src.llm_provider import (
    GeminiNotConfiguredError,
    GeminiProvider,
    GeminiRequestError,
    GeminiResponseError,
    _sanitize_json_schema,
)


class SampleResponse(BaseModel):
    answer: str
    confidence: int


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.last_request = None

    def generate_content(self, **kwargs):
        self.last_request = kwargs

        if self.error is not None:
            raise self.error

        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.models = FakeModels(response=response, error=error)


class FakeResponse:
    def __init__(self, text):
        self.text = text


def test_provider_is_unconfigured_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    provider = GeminiProvider()

    assert provider.is_configured is False

    with pytest.raises(GeminiNotConfiguredError):
        provider.generate_structured("Test prompt", SampleResponse)


def test_provider_reads_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    provider = GeminiProvider()

    assert provider.is_configured is True


def test_provider_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        GeminiProvider(api_key="test-key", timeout_seconds=0)


def test_provider_rejects_empty_prompt():
    provider = GeminiProvider(api_key="test-key")

    with pytest.raises(ValueError):
        provider.generate_structured("   ", SampleResponse)


def test_provider_validates_structured_response():
    client = FakeClient(
        response=FakeResponse('{"answer": "Reviewed", "confidence": 90}')
    )
    provider = GeminiProvider(api_key="test-key", client=client)

    result = provider.generate_structured("Review this clause", SampleResponse)

    assert result.answer == "Reviewed"
    assert result.confidence == 90
    assert client.models.last_request["model"] == provider.model


def test_provider_rejects_invalid_response_schema():
    client = FakeClient(
        response=FakeResponse('{"answer": "Reviewed", "confidence": "high"}')
    )
    provider = GeminiProvider(api_key="test-key", client=client)

    with pytest.raises(GeminiResponseError):
        provider.generate_structured("Review this clause", SampleResponse)


def test_provider_wraps_request_failures():
    client = FakeClient(error=RuntimeError("simulated API failure"))
    provider = GeminiProvider(api_key="test-key", client=client)

    with pytest.raises(GeminiRequestError):
        provider.generate_structured("Review this clause", SampleResponse)


def test_schema_sanitizer_removes_nested_additional_properties():
    schema = {
        "type": "OBJECT",
        "additionalProperties": False,
        "properties": {
            "items": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "STRING"}
                    },
                },
            }
        },
    }

    sanitized = _sanitize_json_schema(schema)

    assert "additionalProperties" not in sanitized
    nested = sanitized["properties"]["items"]["items"]
    assert "additionalProperties" not in nested
    assert nested["properties"]["name"] == {"type": "STRING"}
