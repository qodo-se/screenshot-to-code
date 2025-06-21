import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, call

from backend.llm import stream_openai_response, Llm, Completion
from openai.types.chat import ChatCompletionChunk
from typing import List

@pytest.mark.asyncio
async def test_stream_openai_response_streaming_model_success(mocker):
    # Arrange
    messages = [{"role": "user", "content": "Hello"}]
    api_key = "test-key"
    base_url = "http://test"
    model = Llm.GPT_4O_2024_05_13

    # Mock time
    mocker.patch("backend.llm.time.time", side_effect=[100.0, 102.0])

    # Mock callback
    callback = AsyncMock()

    # Mock AsyncOpenAI and streaming
    mock_client = AsyncMock()
    mock_stream = AsyncMock()
    chunk1 = MagicMock(spec=ChatCompletionChunk)
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "Hello "
    chunk2 = MagicMock(spec=ChatCompletionChunk)
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = "World!"
    mock_stream.__aiter__.return_value = [chunk1, chunk2]
    mock_client.chat.completions.create.return_value = mock_stream
    mocker.patch("backend.llm.AsyncOpenAI", return_value=mock_client)

    # Act
    result = await stream_openai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        callback=callback,
        model=model,
    )

    # Assert
    assert result["code"] == "Hello World!"
    assert pytest.approx(result["duration"], 0.01) == 2.0
    callback.assert_has_calls([call("Hello "), call("World!")])
    mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_stream_openai_response_o1_model_success(mocker):
    # Arrange
    messages = [{"role": "user", "content": "Test O1"}]
    api_key = "test-key"
    base_url = "http://test"
    model = Llm.O1_2024_12_17

    mocker.patch("backend.llm.time.time", side_effect=[10.0, 11.5])

    callback = AsyncMock()

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "O1 response"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mocker.patch("backend.llm.AsyncOpenAI", return_value=mock_client)

    # Act
    result = await stream_openai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        callback=callback,
        model=model,
    )

    # Assert
    assert result["code"] == "O1 response"
    assert pytest.approx(result["duration"], 0.01) == 1.5
    callback.assert_not_awaited()
    mock_client.close.assert_awaited_once()
    # Ensure correct params: no 'stream', has 'max_completion_tokens'
    called_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert called_kwargs["model"] == model.value
    assert called_kwargs["max_completion_tokens"] == 20000
    assert "stream" not in called_kwargs


@pytest.mark.asyncio
async def test_stream_openai_response_callback_invocation(mocker):
    # Arrange
    messages = [{"role": "user", "content": "Callback test"}]
    api_key = "test-key"
    base_url = "http://test"
    model = Llm.GPT_4_VISION

    mocker.patch("backend.llm.time.time", side_effect=[1.0, 2.0])

    callback = AsyncMock()

    mock_client = AsyncMock()
    mock_stream = AsyncMock()
    chunk1 = MagicMock(spec=ChatCompletionChunk)
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "A"
    chunk2 = MagicMock(spec=ChatCompletionChunk)
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = "B"
    chunk3 = MagicMock(spec=ChatCompletionChunk)
    chunk3.choices = [MagicMock()]
    chunk3.choices[0].delta.content = "C"
    mock_stream.__aiter__.return_value = [chunk1, chunk2, chunk3]
    mock_client.chat.completions.create.return_value = mock_stream
    mocker.patch("backend.llm.AsyncOpenAI", return_value=mock_client)

    # Act
    await stream_openai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        callback=callback,
        model=model,
    )

    # Assert
    callback.assert_has_calls([call("A"), call("B"), call("C")])


@pytest.mark.asyncio
async def test_stream_openai_response_empty_chunk_content(mocker):
    # Arrange
    messages = [{"role": "user", "content": "Edge"}]
    api_key = "test-key"
    base_url = "http://test"
    model = Llm.GPT_4O_2024_11_20

    mocker.patch("backend.llm.time.time", side_effect=[5.0, 5.5])

    callback = AsyncMock()

    mock_client = AsyncMock()
    mock_stream = AsyncMock()
    # First chunk: no content
    chunk1 = MagicMock(spec=ChatCompletionChunk)
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = None
    # Second chunk: empty string
    chunk2 = MagicMock(spec=ChatCompletionChunk)
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = ""
    # Third chunk: valid content
    chunk3 = MagicMock(spec=ChatCompletionChunk)
    chunk3.choices = [MagicMock()]
    chunk3.choices[0].delta.content = "Valid"
    mock_stream.__aiter__.return_value = [chunk1, chunk2, chunk3]
    mock_client.chat.completions.create.return_value = mock_stream
    mocker.patch("backend.llm.AsyncOpenAI", return_value=mock_client)

    # Act
    result = await stream_openai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        callback=callback,
        model=model,
    )

    # Assert
    assert result["code"] == "Valid"
    callback.assert_awaited_once_with("Valid")


@pytest.mark.asyncio
async def test_stream_openai_response_empty_messages(mocker):
    # Arrange
    messages = []
    api_key = "test-key"
    base_url = "http://test"
    model = Llm.GPT_4_TURBO_2024_04_09

    mocker.patch("backend.llm.time.time", side_effect=[0.0, 0.1])

    callback = AsyncMock()

    mock_client = AsyncMock()
    mock_stream = AsyncMock()
    chunk = MagicMock(spec=ChatCompletionChunk)
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = "Empty"
    mock_stream.__aiter__.return_value = [chunk]
    mock_client.chat.completions.create.return_value = mock_stream
    mocker.patch("backend.llm.AsyncOpenAI", return_value=mock_client)

    # Act
    result = await stream_openai_response(
        messages=messages,
        api_key=api_key,
        base_url=base_url,
        callback=callback,
        model=model,
    )

    # Assert
    assert result["code"] == "Empty"
    callback.assert_awaited_once_with("Empty")


@pytest.mark.asyncio
async def test_stream_openai_response_api_error_handling(mocker):
    # Arrange
    messages = [{"role": "user", "content": "Error"}]
    api_key = "test-key"
    base_url = "http://test"
    model = Llm.GPT_4O_2024_05_13

    mocker.patch("backend.llm.time.time", side_effect=[1.0, 1.1])

    callback = AsyncMock()

    mock_client = AsyncMock()
    # Simulate error during streaming
    async def error_stream(*args, **kwargs):
        raise RuntimeError("API error")
    mock_client.chat.completions.create.side_effect = error_stream
    mocker.patch("backend.llm.AsyncOpenAI", return_value=mock_client)

    # Act
    with pytest.raises(RuntimeError, match="API error"):
        await stream_openai_response(
            messages=messages,
            api_key=api_key,
            base_url=base_url,
            callback=callback,
            model=model,
        )
    mock_client.close.assert_awaited_once()