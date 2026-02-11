from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.platform.services.inference import (
    InferenceResponse,
    chat_completion,
    is_configured,
    text_completion,
    vision_analysis,
)


def test_is_configured_false_when_no_key():
    with patch("app.platform.services.inference.settings") as mock_settings:
        mock_settings.inference_api_key = None
        assert is_configured() is False


def test_is_configured_false_when_empty_key():
    with patch("app.platform.services.inference.settings") as mock_settings:
        mock_settings.inference_api_key = ""
        assert is_configured() is False


def test_is_configured_true_when_key_set():
    with patch("app.platform.services.inference.settings") as mock_settings:
        mock_settings.inference_api_key = "dop_v1_test_key"
        assert is_configured() is True


@pytest.mark.asyncio
async def test_chat_completion_parses_response():
    api_response = {
        "choices": [{"message": {"content": "Test AI response"}}],
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = api_response
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference.httpx.AsyncClient") as MockClient:
        mock_settings.inference_api_key = "test-key"
        mock_settings.inference_base_url = "https://test.api/v1"
        mock_settings.inference_model = "test-model"
        mock_settings.inference_timeout_seconds = 30.0

        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await chat_completion(messages=[{"role": "user", "content": "hello"}])

    assert isinstance(result, InferenceResponse)
    assert result.text == "Test AI response"
    assert result.model == "test-model"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5


@pytest.mark.asyncio
async def test_chat_completion_handles_empty_choices():
    api_response = {
        "choices": [],
        "model": "test-model",
        "usage": {"prompt_tokens": 5, "completion_tokens": 0},
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = api_response
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference.httpx.AsyncClient") as MockClient:
        mock_settings.inference_api_key = "test-key"
        mock_settings.inference_base_url = "https://test.api/v1"
        mock_settings.inference_model = "test-model"
        mock_settings.inference_timeout_seconds = 30.0

        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await chat_completion(messages=[{"role": "user", "content": "hello"}])

    assert result.text == ""


@pytest.mark.asyncio
async def test_chat_completion_uses_correct_url():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
        "model": "m",
        "usage": {},
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference.httpx.AsyncClient") as MockClient:
        mock_settings.inference_api_key = "key123"
        mock_settings.inference_base_url = "https://cluster-api.do-ai.run/v1/"
        mock_settings.inference_model = "llama-70b"
        mock_settings.inference_timeout_seconds = 30.0

        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        await chat_completion(messages=[{"role": "user", "content": "test"}])

    call_args = mock_client_instance.post.call_args
    assert call_args[0][0] == "https://cluster-api.do-ai.run/v1/chat/completions"
    body = call_args[1]["json"]
    assert body["model"] == "llama-70b"
    headers = call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer key123"


@pytest.mark.asyncio
async def test_vision_analysis_builds_multimodal_messages():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"score": 8}'}}],
        "model": "vision-model",
        "usage": {"prompt_tokens": 100, "completion_tokens": 10},
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference.httpx.AsyncClient") as MockClient:
        mock_settings.inference_api_key = "key"
        mock_settings.inference_base_url = "https://test.api/v1"
        mock_settings.inference_vision_model = "vision-model"
        mock_settings.inference_model = "text-model"
        mock_settings.inference_timeout_seconds = 30.0

        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await vision_analysis(
            prompt="analyze this",
            image_b64_list=["abc123", "def456"],
        )

    assert result.text == '{"score": 8}'
    call_args = mock_client_instance.post.call_args
    body = call_args[1]["json"]
    assert body["model"] == "vision-model"
    messages = body["messages"]
    assert len(messages) == 1
    content = messages[0]["content"]
    assert len(content) == 3
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "analyze this"
    assert content[1]["type"] == "image_url"
    assert "abc123" in content[1]["image_url"]["url"]
    assert content[2]["type"] == "image_url"
    assert "def456" in content[2]["image_url"]["url"]


@pytest.mark.asyncio
async def test_text_completion_builds_system_user_messages():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "explained"}}],
        "model": "text-model",
        "usage": {},
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference.httpx.AsyncClient") as MockClient:
        mock_settings.inference_api_key = "key"
        mock_settings.inference_base_url = "https://test.api/v1"
        mock_settings.inference_model = "text-model"
        mock_settings.inference_timeout_seconds = 30.0

        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await text_completion(
            system_prompt="You are helpful.",
            user_prompt="Explain this.",
        )

    assert result.text == "explained"
    call_args = mock_client_instance.post.call_args
    body = call_args[1]["json"]
    messages = body["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are helpful."
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Explain this."
