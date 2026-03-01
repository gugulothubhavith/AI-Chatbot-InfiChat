# Indian Conversational Voice AI Agent

Complete project for a real-time Indian English conversational assistant optimized for Text-to-Speech output.

## What this includes
- Professional system prompt for Indian corporate support voice.
- Voice profile configuration for tone, pace, pauses, and pronunciation.
- Response engine with tone adaptation.
- TTS formatter for number and abbreviation clarity.
- CLI chat runner.
- HTTP API server for integration.
- Unit tests for key behavior.

## Project structure
```
.
├── app
│   ├── agent.py
│   ├── cli.py
│   ├── config.py
│   ├── http_api.py
│   ├── models.py
│   ├── response_engine.py
│   └── tts_formatter.py
├── tests
│   ├── test_agent.py
│   ├── test_response_engine.py
│   └── test_tts_formatter.py
├── main.py
├── sample_dialogues.md
├── system_prompt.txt
├── voice_config.json
└── pyproject.toml
```

## Prerequisites
- Python 3.10 or later

## Run in CLI mode
```bash
python main.py --mode cli
```

## Run in API mode
```bash
python main.py --mode api --host 0.0.0.0 --port 8080
```

## API endpoints
### Health
```bash
curl -X GET http://127.0.0.1:8080/health
```

### Metadata
```bash
curl -X GET http://127.0.0.1:8080/metadata
```

### Chat
```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I reset my password?"}'
```

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Notes
- Runtime uses Python standard library only.
- Current response generation is deterministic and template-driven.
- No API key is needed.
