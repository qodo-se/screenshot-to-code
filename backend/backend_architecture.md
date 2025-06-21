# Screenshot-to-Code Backend Architecture

```mermaid
graph TD
    %% Main Application Components
    Client[Frontend Client] --> |HTTP Requests| FastAPI[FastAPI Server]
    FastAPI --> |Routes Requests| Router[API Routers]
    
    %% API Routes
    Router --> ScreenshotRoute[Screenshot Route]
    Router --> GenerateCodeRoute[Generate Code Route]
    Router --> HomeRoute[Home Route]
    Router --> EvalsRoute[Evals Route]
    
    %% Core Processing Components
    ScreenshotRoute --> |Process Images| ImageProcessing[Image Processing]
    GenerateCodeRoute --> |Generate Code| LLM[LLM Service]
    
    %% LLM Service
    LLM --> |OpenAI| OpenAIStream[OpenAI Stream]
    LLM --> |Claude| ClaudeStream[Claude Stream]
    LLM --> |Gemini| GeminiStream[Gemini Stream]
    LLM --> |DeepSeek| DeepSeekStream[DeepSeek Stream]
    
    %% Image Generation
    GenerateCodeRoute --> |Generate Images| ImageGen[Image Generation]
    ImageGen --> |DALL-E| DalleGen[DALL-E]
    ImageGen --> |Replicate| ReplicateGen[Replicate]
    
    %% Video Processing
    VideoToApp[Video to App] --> |Process Video| VideoUtils[Video Utils]
    VideoToApp --> |Generate Code| LLM
    
    %% Evaluation System
    EvalsRoute --> |Run Evaluations| Evals[Evaluation System]
    
    %% Supporting Services
    LLM --> |Debug| Debug[Debug System]
    LLM --> |Prompts| Prompts[Prompt Templates]
    
    %% Configuration
    Config[Configuration] --> FastAPI
    Config --> LLM
    Config --> ImageGen
    
    %% File System Logging
    FSLogging[FS Logging] --> LLM
    FSLogging --> ImageGen
    FSLogging --> VideoToApp
    
    %% Codegen Utilities
    CodegenUtils[Codegen Utils] --> GenerateCodeRoute
    
    %% WebSocket Support
    WS[WebSocket] --> FastAPI
    
    %% Style definitions
    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    classDef service fill:#bbf,stroke:#333,stroke-width:1px;
    classDef route fill:#bfb,stroke:#333,stroke-width:1px;
    classDef util fill:#fbb,stroke:#333,stroke-width:1px;
    
    %% Apply styles
    class FastAPI,LLM,ImageGen,VideoToApp core;
    class OpenAIStream,ClaudeStream,GeminiStream,DeepSeekStream,DalleGen,ReplicateGen service;
    class ScreenshotRoute,GenerateCodeRoute,HomeRoute,EvalsRoute route;
    class Config,Prompts,Debug,FSLogging,CodegenUtils,VideoUtils,WS,ImageProcessing util;
```

## Component Descriptions

### Core Components
- **FastAPI Server**: Main entry point for the application, handles HTTP requests
- **LLM Service**: Manages interactions with various language models (OpenAI, Claude, Gemini, DeepSeek)
- **Image Generation**: Handles image generation using DALL-E or Replicate
- **Video to App**: Processes video input and generates corresponding application code

### API Routes
- **Screenshot Route**: Handles screenshot uploads and processing
- **Generate Code Route**: Manages code generation from screenshots or designs
- **Home Route**: Basic application information and status
- **Evals Route**: Endpoints for evaluation and testing

### Supporting Services
- **Image Processing**: Utilities for processing and optimizing images
- **Debug System**: Tools for debugging and logging
- **Prompt Templates**: Predefined prompts for different LLM services
- **Configuration**: Application configuration and environment variables
- **FS Logging**: File system logging utilities
- **Codegen Utils**: Utilities for code generation
- **WebSocket**: WebSocket support for real-time communication
- **Video Utils**: Utilities for video processing

### LLM Providers
- **OpenAI Stream**: Integration with OpenAI models (GPT-4 Vision, GPT-4o)
- **Claude Stream**: Integration with Anthropic's Claude models
- **Gemini Stream**: Integration with Google's Gemini models
- **DeepSeek Stream**: Integration with DeepSeek models

### Image Generation Providers
- **DALL-E**: Integration with OpenAI's DALL-E for image generation
- **Replicate**: Integration with Replicate for image generation
```