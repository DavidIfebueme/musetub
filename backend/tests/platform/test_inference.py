from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.platform.services.inference import (
    InferenceResponse,
    chat_completion,
    is_configured,
    text_completion,
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
        mock_settings.inference_api_key = "sk-do-test-key"
        assert is_configured() is True


def _mock_completion_response(content="Test AI response", model="llama3.3-70b-instruct", prompt_tokens=10, completion_tokens=5):
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens

    message = MagicMock()
    message.content = content

    choice = MagicMock()
    choice.message = message

    resp = MagicMock()
    resp.choices = [choice]
    resp.model = model
    resp.usage = usage
    return resp


@pytest.mark.asyncio
async def test_chat_completion_parses_response():
    mock_resp = _mock_completion_response()
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference._get_client", return_value=mock_client):
        mock_settings.inference_api_key = "test-key"
        mock_settings.inference_model = "llama3.3-70b-instruct"

        result = await chat_completion(messages=[{"role": "user", "content": "hello"}])

    assert isinstance(result, InferenceResponse)
    assert result.text == "Test AI response"
    assert result.model == "llama3.3-70b-instruct"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5


@pytest.mark.asyncio
async def test_chat_completion_handles_empty_choices():
    mock_resp = MagicMock()
    mock_resp.choices = []
    mock_resp.model = "llama3.3-70b-instruct"
    mock_resp.usage = None

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference._get_client", return_value=mock_client):
        mock_settings.inference_api_key = "test-key"
        mock_settings.inference_model = "llama3.3-70b-instruct"

        result = await chat_completion(messages=[{"role": "user", "content": "hello"}])

    assert result.text == ""


@pytest.mark.asyncio
async def test_chat_completion_uses_correct_model():
    mock_resp = _mock_completion_response(model="llama3.3-70b-instruct")
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference._get_client", return_value=mock_client):
        mock_settings.inference_api_key = "key123"
        mock_settings.inference_model = "llama3.3-70b-instruct"

        await chat_completion(messages=[{"role": "user", "content": "test"}])

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "llama3.3-70b-instruct"


@pytest.mark.asyncio
async def test_chat_completion_custom_model():
    mock_resp = _mock_completion_response(model="llama3-8b-instruct")
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference._get_client", return_value=mock_client):
        mock_settings.inference_api_key = "key123"
        mock_settings.inference_model = "llama3.3-70b-instruct"

        await chat_completion(
            messages=[{"role": "user", "content": "test"}],
            model="llama3-8b-instruct",
        )

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "llama3-8b-instruct"


@pytest.mark.asyncio
async def test_text_completion_builds_system_user_messages():
    mock_resp = _mock_completion_response(content="explained")
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference._get_client", return_value=mock_client):
        mock_settings.inference_api_key = "key"
        mock_settings.inference_model = "llama3.3-70b-instruct"

        result = await text_completion(
            system_prompt="You are helpful.",
            user_prompt="Explain this.",
        )

    assert result.text == "explained"
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are helpful."
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Explain this."


@pytest.mark.asyncio
async def test_chat_completion_passes_temperature_and_max_tokens():
    mock_resp = _mock_completion_response()
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    with patch("app.platform.services.inference.settings") as mock_settings, \
         patch("app.platform.services.inference._get_client", return_value=mock_client):
        mock_settings.inference_api_key = "key"
        mock_settings.inference_model = "llama3.3-70b-instruct"

        await chat_completion(
            messages=[{"role": "user", "content": "test"}],
            temperature=0.7,
            max_tokens=2048,
        )

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["temperature"] == 0.7
    assert call_kwargs["max_tokens"] == 2048
