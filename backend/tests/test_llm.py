import pytest
from pytest_mock import MockerFixture
import base64
from typing import List, Any
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk
from anthropic.types import Message, MessageStream, MessageStreamEvent
from google.genai import types

from llm import Llm, stream_openai_response, stream_claude_response, stream_gemini_response
from image_processing.utils import process_image

@pytest.mark.asyncio
async def test_openai_response_streaming(mocker: MockerFixture):
    mock_client = mocker.AsyncMock()
    mock_chunk = mocker.Mock(spec=ChatCompletionChunk)
    mock_chunk.choices = [mocker.Mock(delta=mocker.Mock(content="test content"))]
    mock_client.chat.completions.create.return_value.__aiter__.return_value = [mock_chunk]
    
    mocker.patch('llm.AsyncOpenAI', return_value=mock_client)
    mocker.patch('time.time', side_effect=[0, 1])
    
    messages = [{"role": "user", "content": "test"}]
    callback = mocker.AsyncMock()
    
    result = await stream_openai_response(
        messages=messages,
        api_key="test_key",
        base_url=None,
        callback=callback,
        model=Llm.GPT_4_TURBO_2024_04_09
    )
    
    assert result["duration"] == 1
    assert result["code"] == "test content"
    assert callback.call_count == 1


@pytest.mark.asyncio
async def test_claude_response_streaming(mocker: MockerFixture):
    mock_client = mocker.AsyncMock()
    mock_chunk = mocker.Mock(spec=ChatCompletionChunk)
    mock_chunk.choices = [mocker.Mock(delta=mocker.Mock(content="test content"))]
    mock_client.chat.completions.create.return_value.__aiter__.return_value = [mock_chunk]

    mocker.patch('llm.AsyncAnthropic', return_value=mock_client)
    mocker.patch('time.time', side_effect=[0, 1])

    messages = [{"role": "user", "content": "test"}]
    callback = mocker.AsyncMock()

    result = await stream_claude_response(
        messages=messages,
        api_key="test_key",
        callback=callback,
        model=Llm.CLAUDE_3_OPUS
    )

    assert result["duration"] == 1
    assert result["code"] == "test content"
    assert callback.call_count == 1

@pytest.mark.asyncio
async def test_claude_image_streaming(mocker: MockerFixture):
    mock_client = mocker.AsyncMock()
    mock_stream = mocker.AsyncMock()
    mock_stream.text_stream = ["test response"]
    mock_stream.get_final_message.return_value = mocker.Mock(
        content=[mocker.Mock(text="final response")]
    )
    mock_client.messages.stream.return_value.__aenter__.return_value = mock_stream
    
    mocker.patch('llm.AsyncAnthropic', return_value=mock_client)
    mocker.patch('time.time', side_effect=[0, 2])
    mocker.patch('llm.process_image', return_value=("image/jpeg", "base64data"))
    
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,test"}}]}
    ]
    callback = mocker.AsyncMock()
    
    result = await stream_claude_response(
        messages=messages,
        api_key="test_key",
        callback=callback,
        model=Llm.CLAUDE_3_OPUS
    )
    
    assert result["duration"] == 2
    assert result["code"] == "final response"

@pytest.mark.asyncio
async def test_gemini_base64_image_streaming(mocker: MockerFixture):
    mock_client = mocker.AsyncMock()
    mock_response = mocker.AsyncMock()
    mock_response.text = "test response"
    mock_client.aio.models.generate_content_stream.return_value.__aiter__.return_value = [mock_response]
    
    mocker.patch('genai.Client', return_value=mock_client)
    mocker.patch('time.time', side_effect=[0, 1])
    mocker.patch('base64.b64decode', return_value=b"test_image_data")
    
    messages = [
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,test"}}]}
    ]
    callback = mocker.AsyncMock()
    
    result = await stream_gemini_response(
        messages=messages,
        api_key="test_key",
        callback=callback,
        model=Llm.GEMINI_2_0_FLASH_EXP
    )
    
    assert result["duration"] == 1
    assert result["code"] == "test response"

@pytest.mark.asyncio
async def test_api_timeout_handling(mocker: MockerFixture):
    mock_client = mocker.AsyncMock()
    mock_client.chat.completions.create.side_effect = TimeoutError("API timeout")
    
    mocker.patch('llm.AsyncOpenAI', return_value=mock_client)
    
    messages = [{"role": "user", "content": "test"}]
    callback = mocker.AsyncMock()
    
    with pytest.raises(TimeoutError):
        await stream_openai_response(
            messages=messages,
            api_key="test_key",
            base_url=None,
            callback=callback,
            model=Llm.GPT_4_TURBO_2024_04_09
        )

@pytest.mark.asyncio
async def test_invalid_image_handling(mocker: MockerFixture):
    mock_process_image = mocker.patch('llm.process_image')
    mock_process_image.side_effect = ValueError("Invalid image data")
    
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "invalid_data"}}]}
    ]
    callback = mocker.AsyncMock()
    
    with pytest.raises(ValueError):
        await stream_claude_response(
            messages=messages,
            api_key="test_key",
            callback=callback,
            model=Llm.CLAUDE_3_OPUS
        )

@pytest.mark.asyncio
async def test_invalid_message_handling(mocker: MockerFixture):
    mock_client = mocker.AsyncMock()
    mocker.patch('llm.AsyncOpenAI', return_value=mock_client)
    
    messages: List[ChatCompletionMessageParam] = []
    callback = mocker.AsyncMock()
    
    with pytest.raises(Exception):
        await stream_openai_response(
            messages=messages,
            api_key="test_key",
            base_url=None,
            callback=callback,
            model=Llm.GPT_4_TURBO_2024_04_09
        )