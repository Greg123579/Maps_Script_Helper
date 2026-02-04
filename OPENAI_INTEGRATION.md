# OpenAI Integration - Summary of Changes

## Overview
The application now supports both **Google Gemini** and **OpenAI** models for the AI Assistant. Users can select their preferred provider and model from the AI Assistant sidebar.

## Supported Models

### Google Gemini Models
- `gemini-2.5-flash-lite` (fast, default)
- `gemini-2.5-pro` (best quality)

### OpenAI Models
- `gpt-4o-mini` (fast, affordable, default)
- `gpt-4o` (high intelligence)
- `gpt-4.1-mini` (fast)
- `gpt-4.1` (best quality)

## Changes Made

### Backend (`backend/app.py`)
1. **Added OpenAI SDK import**: `from openai import OpenAI`
2. **Updated environment configuration**: Added `OPENAI_API_KEY` environment variable support
3. **Updated `ChatRequest` model**: 
   - Added `provider` field (gemini/openai)
   - Added `openai_api_key` field for user-provided OpenAI keys
4. **Enhanced chat endpoint** (`/api/chat`):
   - Auto-detects provider from model name (gpt-* → openai, gemini-* → gemini)
   - Validates API keys based on selected provider
   - Routes requests to appropriate AI service (Gemini or OpenAI)
   - Formats conversation history according to each provider's requirements
   - Handles provider-specific error messages

### Frontend (`frontend/app.jsx`)
1. **Added state management**:
   - `aiProvider`: Tracks selected provider (gemini/openai)
   - `openaiApiKey`: Stores OpenAI API key in localStorage
   - `showOpenaiApiKey`: Toggle visibility for OpenAI key input
2. **Added provider selection**:
   - New dropdown in AI Assistant sidebar to choose between Google Gemini and OpenAI
   - Model dropdown dynamically updates based on selected provider
3. **API key configuration**:
   - Both API keys are loaded from and saved to localStorage
   - New Settings section for OpenAI API key configuration
   - Added helpful links to get API keys for both providers
4. **API call updates**:
   - Sends both `provider` and `openai_api_key` to backend
   - Provider automatically switches when model changes

### Dependencies (`backend/requirements.txt`)
- Added `openai==1.58.1`

### Docker Configuration (`docker-compose.yml`)
- Updated to support `OPENAI_API_KEY` environment variable
- Changed API keys to use environment variable substitution: `${GOOGLE_API_KEY:-}` and `${OPENAI_API_KEY:-}`
- **SECURITY NOTE**: Removed hardcoded API keys. Users should now set keys via environment variables or `.env` file

## How to Use

### Setting Up API Keys

#### Option 1: Via Browser (Recommended for Users)
1. Go to the **Settings** tab
2. Enter your Google Gemini API key in the "Google Gemini API Configuration" section
3. Enter your OpenAI API key in the "OpenAI API Configuration" section
4. Keys are stored in your browser's localStorage

#### Option 2: Via Environment Variables (For Docker/Server)
1. Create a `.env` file in the project root:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```
2. The keys will be available to the Docker container

### Using the AI Assistant
1. Open the **Code** or **Output** tab to see the AI Assistant sidebar
2. Select your preferred **AI Provider** (Google Gemini or OpenAI)
3. Choose your desired **AI Model** from the dropdown
4. Start chatting! The assistant will use the selected provider and model

### Getting API Keys
- **Google Gemini**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## Technical Details

### Provider Auto-Detection
The system automatically detects the provider based on the model name:
- Models starting with `gpt-` → OpenAI
- Models starting with `gemini-` → Google Gemini
- Falls back to explicit `provider` parameter if set

### Image Support
Currently, image analysis is only supported with Google Gemini models. When using OpenAI, image context is added as text description only.

### Error Handling
The backend provides user-friendly error messages for:
- Missing API keys
- Invalid API keys
- Rate limiting
- Content safety filters
- Timeouts

## Notes
- API keys are never stored on the server
- Keys are only sent to the respective AI provider (Google or OpenAI)
- The default provider is Google Gemini for backward compatibility
- Users can switch providers at any time without losing chat history
