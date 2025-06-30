# Design Patterns and Best Practices

This document outlines the key design patterns and best practices employed in this codebase.

## 1. API Development with FastAPI

The backend is built using [FastAPI](https://fastapi.tiangolo.com/), a modern, high-performance web framework for Python. FastAPI's design encourages the use of type hints, which improves code clarity and reduces bugs.

**Example (`backend/main.py`):**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import screenshot, generate_code, home, evals

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

# Configure CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes
app.include_router(generate_code.router)
app.include_router(screenshot.router)
app.include_router(home.router)
app.include_router(evals.router)
```

## 2. Modular Routing

To keep the codebase organized and maintainable, API routes are defined in separate modules within the `backend/routes` directory. These routers are then included in the main FastAPI application.

**Example (`backend/routes/generate_code.py`):**
```python
from fastapi import APIRouter

router = APIRouter()

@router.websocket("/generate-code")
async def stream_code(websocket: WebSocket):
    # ... implementation
```

## 3. Asynchronous Operations with `asyncio`

The application leverages `asyncio` to handle concurrent I/O-bound operations efficiently. This is particularly important for managing WebSocket connections and making API calls to external services like language models. The use of `async` and `await` is prevalent throughout the codebase.

**Example (`backend/routes/generate_code.py`):**
```python
import asyncio

# ...

tasks = [
    perform_image_generation(
        completion,
        should_generate_images,
        openai_api_key,
        openai_base_url,
        image_cache,
    )
    for completion in completions
]

updated_completions = await asyncio.gather(*image_generation_tasks)
```

## 4. WebSockets for Real-time Communication

For features like real-time code generation, the application uses WebSockets to maintain a persistent connection with the client. This allows the server to stream data as it becomes available, providing a more responsive user experience.

**Example (`backend/routes/generate_code.py`):**
```python
from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/generate-code")
async def stream_code(websocket: WebSocket):
    await websocket.accept()
    # ... handle WebSocket communication
```

## 5. Strategy Pattern for Model Selection

The application employs a strategy pattern to select the appropriate language model for code generation based on available API keys and user-specified settings. This allows for flexibility and easy integration of new models in the future.

**Example (`backend/routes/generate_code.py`):**
```python
if openai_api_key and anthropic_api_key:
    variant_models = [
        claude_model,
        Llm.GPT_4O_2024_11_20,
    ]
elif openai_api_key:
    variant_models = [
        Llm.GPT_4O_2024_11_20,
        Llm.GPT_4O_2024_11_20,
    ]
elif anthropic_api_key:
    variant_models = [
        claude_model,
        Llm.CLAUDE_3_5_SONNET_2024_06_20,
    ]
else:
    await throw_error(
        "No OpenAI or Anthropic API key found."
    )
```

## 6. Structured Data with Dataclasses

Dataclasses are used to create simple, yet structured, data objects. This improves code readability and makes it easier to manage data that is passed between different parts of the application.

**Example (`backend/routes/generate_code.py`):**
```python
from dataclasses import dataclass

@dataclass
class ExtractedParams:
    stack: Stack
    input_mode: InputMode
    should_generate_images: bool
    openai_api_key: str | None
    anthropic_api_key: str | None
    openai_base_url: str | None
    generation_type: Literal["create", "update"]
```

## 7. Centralized Configuration Management

Configuration is managed centrally through a `config.py` file and environment variables. A helper function is used to resolve settings, providing a clear order of precedence.

**Example (`backend/routes/generate_code.py`):**
```python
def get_from_settings_dialog_or_env(
    params: dict[str, str], key: str, env_var: str | None
) -> str | None:
    value = params.get(key)
    if value:
        print(f"Using {key} from client-side settings dialog")
        return value

    if env_var:
        print(f"Using {key} from environment variable")
        return env_var

    return None
```

## 8. Robust Error Handling

The application includes specific error handling for external API calls and provides a mechanism for sending detailed error messages to the client over the WebSocket connection.

**Example (`backend/routes/generate_code.py`):**
```python
except openai.AuthenticationError as e:
    print("[GENERATE_CODE] Authentication failed", e)
    error_message = (
        "Incorrect OpenAI key."
    )
    return await throw_error(error_message)
except openai.NotFoundError as e:
    print("[GENERATE_CODE] Model not found", e)
    error_message = (
        e.message
    )
    return await throw_error(error_message)
```
