import copy
from enum import Enum
import base64
import time
import os
from typing import Any, Awaitable, Callable, List, cast, TypedDict
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk
import httpx
from dotenv import load_dotenv
from config import IS_DEBUG_ENABLED
from debug.DebugFileWriter import DebugFileWriter
from image_processing.utils import process_image
from google import genai
from google.genai import types

from utils import pprint_prompt

# Load environment variables from .env file if present
load_dotenv()


# Actual model versions that are passed to the LLMs and stored in our logs
class Llm(Enum):
    GPT_4_VISION = "gpt-4-vision-preview"
    GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09"
    GPT_4O_2024_05_13 = "gpt-4o-2024-05-13"
    GPT_4O_2024_08_06 = "gpt-4o-2024-08-06"
    GPT_4O_2024_11_20 = "gpt-4o-2024-11-20"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_5_SONNET_2024_06_20 = "claude-3-5-sonnet-20240620"
    CLAUDE_3_5_SONNET_2024_10_22 = "claude-3-5-sonnet-20241022"
    GEMINI_2_0_FLASH_EXP = "gemini-2.0-flash-exp"
    O1_2024_12_17 = "o1-2024-12-17"
    DEEPSEEK_CODER = "deepseek-coder"

# DeepSeek Configuration - Load from environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE_URL = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1")

class Completion(TypedDict):
    duration: float
    code: str


async def stream_openai_response(
    messages: List[ChatCompletionMessageParam],
    api_key: str,
    base_url: str | None,
    callback: Callable[[str], Awaitable[None]],
    model: Llm,
) -> Completion:
    start_time = time.time()
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # Base parameters
    params = {
        "model": model.value,
        "messages": messages,
        "timeout": 600,
    }

    # O1 doesn't support streaming or temperature
    if model != Llm.O1_2024_12_17:
        params["temperature"] = 0
        params["stream"] = True

    # Add 'max_tokens' corresponding to the model
    if model == Llm.GPT_4O_2024_05_13:
        params["max_tokens"] = 4096

    if model == Llm.GPT_4O_2024_11_20:
        params["max_tokens"] = 16384

    if model == Llm.O1_2024_12_17:
        params["max_completion_tokens"] = 20000

    # O1 doesn't support streaming
    if model == Llm.O1_2024_12_17:
        response = await client.chat.completions.create(**params)  # type: ignore
        full_response = response.choices[0].message.content  # type: ignore
    else:
        stream = await client.chat.completions.create(**params)  # type: ignore
        full_response = ""
        async for chunk in stream:  # type: ignore
            assert isinstance(chunk, ChatCompletionChunk)
            if (
                chunk.choices
                and len(chunk.choices) > 0
                and chunk.choices[0].delta
                and chunk.choices[0].delta.content
            ):
                content = chunk.choices[0].delta.content or ""
                full_response += content
                await callback(content)

    await client.close()

    completion_time = time.time() - start_time
    return {"duration": completion_time, "code": full_response}


# TODO: Have a seperate function that translates OpenAI messages to Claude messages
async def stream_claude_response(
    messages: List[ChatCompletionMessageParam],
    api_key: str,
    callback: Callable[[str], Awaitable[None]],
    model: Llm,
) -> Completion:
    start_time = time.time()
    client = AsyncAnthropic(api_key=api_key)

    # Base parameters
    max_tokens = 8192
    temperature = 0.0

    # Translate OpenAI messages to Claude messages

    # Deep copy messages to avoid modifying the original list
    cloned_messages = copy.deepcopy(messages)

    system_prompt = cast(str, cloned_messages[0].get("content"))
    claude_messages = [dict(message) for message in cloned_messages[1:]]
    for message in claude_messages:
        if not isinstance(message["content"], list):
            continue

        for content in message["content"]:  # type: ignore
            if content["type"] == "image_url":
                content["type"] = "image"

                # Extract base64 data and media type from data URL
                # Example base64 data URL: data:image/png;base64,iVBOR...
                image_data_url = cast(str, content["image_url"]["url"])

                # Process image and split media type and data
                # so it works with Claude (under 5mb in base64 encoding)
                (media_type, base64_data) = process_image(image_data_url)

                # Remove OpenAI parameter
                del content["image_url"]

                content["source"] = {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_data,
                }

    # Stream Claude response
    async with client.messages.stream(
        model=model.value,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=claude_messages,  # type: ignore
        extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"},
    ) as stream:
        async for text in stream.text_stream:
            await callback(text)

    # Return final message
    response = await stream.get_final_message()

    # Close the Anthropic client
    await client.close()

    completion_time = time.time() - start_time
    return {"duration": completion_time, "code": response.content[0].text}


async def stream_claude_response_native(
    system_prompt: str,
    messages: list[Any],
    api_key: str,
    callback: Callable[[str], Awaitable[None]],
    include_thinking: bool = False,
    model: Llm = Llm.CLAUDE_3_OPUS,
) -> Completion:
    start_time = time.time()
    client = AsyncAnthropic(api_key=api_key)

    # Base model parameters
    max_tokens = 4096
    temperature = 0.0

    # Multi-pass flow
    current_pass_num = 1
    max_passes = 2

    prefix = "<thinking>"
    response = None

    # For debugging
    full_stream = ""
    debug_file_writer = DebugFileWriter()

    while current_pass_num <= max_passes:
        current_pass_num += 1

        # Set up message depending on whether we have a <thinking> prefix
        messages_to_send = (
            messages + [{"role": "assistant", "content": prefix}]
            if include_thinking
            else messages
        )

        pprint_prompt(messages_to_send)

        async with client.messages.stream(
            model=model.value,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages_to_send,  # type: ignore
        ) as stream:
            async for text in stream.text_stream:
                print(text, end="", flush=True)
                full_stream += text
                await callback(text)

        response = await stream.get_final_message()
        response_text = response.content[0].text

        # Write each pass's code to .html file and thinking to .txt file
        if IS_DEBUG_ENABLED:
            debug_file_writer.write_to_file(
                f"pass_{current_pass_num - 1}.html",
                debug_file_writer.extract_html_content(response_text),
            )
            debug_file_writer.write_to_file(
                f"thinking_pass_{current_pass_num - 1}.txt",
                response_text.split("</thinking>")[0],
            )

        # Set up messages array for next pass
        messages += [
            {"role": "assistant", "content": str(prefix) + response.content[0].text},
            {
                "role": "user",
                "content": "You've done a good job with a first draft. Improve this further based on the original instructions so that the app is fully functional and looks like the original video of the app we're trying to replicate.",
            },
        ]

        print(
            f"Token usage: Input Tokens: {response.usage.input_tokens}, Output Tokens: {response.usage.output_tokens}"
        )

    # Close the Anthropic client
    await client.close()

    completion_time = time.time() - start_time

    if IS_DEBUG_ENABLED:
        debug_file_writer.write_to_file("full_stream.txt", full_stream)

    if not response:
        raise Exception("No HTML response found in AI response")
    else:
        return {
            "duration": completion_time,
            "code": response.content[0].text,  # type: ignore
        }


async def stream_gemini_response(
    messages: List[ChatCompletionMessageParam],
    api_key: str,
    callback: Callable[[str], Awaitable[None]],
    model: Llm,
) -> Completion:
    start_time = time.time()

    # Extract image URLs from messages
    image_urls = []
    for content_part in messages[-1]["content"]:  # type: ignore
        if content_part["type"] == "image_url":  # type: ignore
            image_url = content_part["image_url"]["url"]  # type: ignore
            if image_url.startswith("data:"):  # type: ignore
                # Extract base64 data and mime type for data URLs
                mime_type = image_url.split(";")[0].split(":")[1]  # type: ignore
                base64_data = image_url.split(",")[1]  # type: ignore
                image_urls = [{"mime_type": mime_type, "data": base64_data}]  # type: ignore
            else:
                # Store regular URLs
                image_urls = [{"uri": image_url}]  # type: ignore
            break  # Exit after first image URL

    client = genai.Client(api_key=api_key)  # type: ignore
    full_response = ""
    async for response in client.aio.models.generate_content_stream(  # type: ignore
        model=model.value,
        contents={
            "parts": [
                {"text": messages[0]["content"]},  # type: ignore
                types.Part.from_bytes(  # type: ignore
                    data=base64.b64decode(image_urls[0]["data"]),  # type: ignore
                    mime_type=image_urls[0]["mime_type"],  # type: ignore
                ),
            ]  # type: ignore
        },  # type: ignore
        config=types.GenerateContentConfig(  # type: ignore
            temperature=0, max_output_tokens=8192
        ),
    ):  # type: ignore
        if response.text:  # type: ignore
            full_response += response.text  # type: ignore
            await callback(response.text)  # type: ignore
    completion_time = time.time() - start_time
    return {"duration": completion_time, "code": full_response}


async def stream_deepseek_response(
    messages: List[ChatCompletionMessageParam],
    api_key: str,
    callback: Callable[[str], Awaitable[None]],
    model: Llm,
) -> Completion:
    """
    Streams responses from the DeepSeek API.

    Note: DeepSeek's API might behave differently regarding streaming
    and message formats compared to OpenAI or Claude. Adjustments might be needed
    based on their specific documentation.
    """
    start_time = time.time()

    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Message Format Translation
    deepseek_messages = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")

        if isinstance(content, list):
             # Assuming text content for now, might need image handling logic
             text_parts = [part.get("text") for part in content if part.get("type") == "text"]
             content_str = "\n".join(filter(None, text_parts))
             # TODO: Add image handling if DeepSeek supports multimodal input
        else:
            content_str = content

        if role and content_str:
            deepseek_messages.append({"role": role, "content": content_str})
        elif role and not content_str and role == 'system':
             deepseek_messages.append({"role": role, "content": ""})

    # API Call
    payload = {
        "model": model.value,
        "messages": deepseek_messages,
        "max_tokens": 4096,
        "temperature": 0,
        "stream": True,
    }

    endpoint = f"{DEEPSEEK_API_BASE_URL}/chat/completions"
    full_response = ""

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                response.raise_for_status()

                # Process the stream - DeepSeek might use Server-Sent Events (SSE)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_json = line[len("data: "):]
                        if data_json.strip() == "[DONE]":
                            break
                        try:
                            chunk = httpx.Response(status_code=200, json=data_json).json()
                            if (
                                chunk.get("choices")
                                and len(chunk["choices"]) > 0
                                and chunk["choices"][0].get("delta")
                                and chunk["choices"][0]["delta"].get("content")
                            ):
                                content = chunk["choices"][0]["delta"]["content"] or ""
                                full_response += content
                                await callback(content)
                        except Exception as json_e:
                            print(f"Error parsing DeepSeek stream chunk: {json_e} - Line: {line}")

    except httpx.HTTPStatusError as e:
        print(f"DeepSeek API request failed: {e.response.status_code}")
        print(f"Response body: {await e.response.aread()}")
        raise Exception(f"DeepSeek API error: {e.response.status_code}") from e
    except Exception as e:
        print(f"An unexpected error occurred calling DeepSeek: {e}")
        raise

    completion_time = time.time() - start_time
    print(f"DeepSeek completion finished in {completion_time:.2f}s")
    return {"duration": completion_time, "code": full_response}
