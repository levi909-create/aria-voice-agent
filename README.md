# Aria — AI Voice Agent

Aria is a conversational voice assistant powered by Claude AI. You speak, she listens, thinks, and talks back in a natural human voice.

## What she can do

- Answer questions and hold a full conversation with memory
- Search the web for current news and information
- Read and write files on your computer
- Run Python code to solve math or data problems
- Tell you the current date and time

## How it works

1. **You speak** — your mic is captured and transcribed by OpenAI Whisper
2. **Claude thinks** — your words are sent to Claude (claude-sonnet-4-6) which reasons and decides if it needs to use any tools
3. **Aria speaks** — the response is converted to natural speech by ElevenLabs and played through your speakers

## Stack

| Layer | Technology |
|---|---|
| AI Brain | Anthropic Claude (claude-sonnet-4-6) |
| Speech to Text | OpenAI Whisper (faster-whisper) |
| Text to Speech | ElevenLabs (Sarah voice) |
| Web Search | DuckDuckGo |
| Audio I/O | sounddevice |

## Setup

1. Clone the repo
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ELEVENLABS_API_KEY=your_key_here
   ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
   ```
4. Run:
   ```
   venv\Scripts\python.exe main.py
   ```

## Voice commands

| Say | Action |
|---|---|
| Anything | Aria responds |
| "clear history" | Resets the conversation |
| "goodbye" / "bye" | Exits |
