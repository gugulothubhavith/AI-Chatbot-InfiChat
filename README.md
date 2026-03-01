<p align="center">
  <img src="cover.png" width="100%" alt="InfiChat">
</p>

<p align="center">
  <img src="frontend/dist/app_name.png" height="60" alt="InfiChat">
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python 3.11"></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/react-18-61dafb.svg" alt="React 18"></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/docker-ready-2496ed.svg" alt="Docker Ready"></a>
  <img src="https://img.shields.io/badge/version-2.0.0-10A37F.svg" alt="Version 2.0.0">
</p>

> **Your Private, Sovereign AI Platform.**
> A production-grade, fully self-hosted AI chatbot with streaming chat, professional Indic TTS/STT, RAG, and sandboxed code execution — all running locally on your own hardware.

---

## 🛡️ Our Mission

In an era of centralized AI, we believe **intelligence should be sovereign**. InfiChat lets you run cutting-edge Generative AI entirely on your own hardware — no data leaves your network.

- **100% Offline Capable**: Run models without an internet connection using Ollama.
- **Zero 3rd Party Tracking**: Your conversations, files, and voice data are yours alone.
- **Data Residency**: All inference, vector storage, and logs stay local.

---

## ✨ Core Features

### 💬 Streaming Multi-Model Chat

- **Groq** — Llama 3.3 70B at ~300 tokens/sec
- **Google Gemini** — Flash 2.0 for vision & multimodal tasks
- **OpenRouter** — Access DeepSeek V3, Claude, and more
- **Ollama** — Local models (fully offline)

### 🎙️ Professional Indic TTS / STT

- **4 Premium Voice Profiles** powered by Edge-TTS:
  - 🔊 **Professional - English (Male)** — `en-IN-PrabhatNeural`
  - 🔊 **Corporate - Hindi (Female)** — `hi-IN-SwaraNeural`
  - 🔊 **Empathetic - Telugu (Male)** — `te-IN-MohanNeural`
  - 🔊 **Alert - Hindi (Fast)** — Hindi @+25% speed
- **Real-Time MP3 Streaming** — Audio starts in <1 second
- **Whisper STT** — Voice-to-text transcription (local, via Faster Whisper)
- Native text normalization: Lakhs/Crores, ₹ currency, Indian abbreviations

### 📚 RAG — Talk to Your Documents

- Upload **PDF, DOCX, or TXT** files to your personal Knowledge Base
- **Semantic search** via ChromaDB + sentence transformers
- Context-aware responses grounded in your documents

### 🤖 Sandboxed Code Agent

- AI writes, runs, and debugs Python code in a **hardened Docker container**
- Real-time output streaming via WebSocket

### � Authentication & Accounts

- **Email + OTP** two-factor authentication
- **Google OAuth 2.0** single sign-on
- JWT-based sessions with password management
- PII scrubbing, session archiving, and shared chat links

### 🖼️ Image Generation

- Stable Diffusion XL via Pollinations / local SDXL

---

## ⚡ Quick Start (Windows)

```powershell
# 1. Clone the repository
git clone https://github.com/gugulothubhavith/Self-Hosted-Generative-AI-Chatbot.git
cd Self-Hosted-Generative-AI-Chatbot

# 2. Run the automated setup
.\setup_windows.ps1
```

**The script will automatically:**

1. Verify system requirements (Docker, Python 3.11+)
2. Configure your `.env` file with API keys
3. Build and launch all Docker containers
4. Open the UI at `http://localhost:5173`

---

## 🗝️ API Keys Required

| Provider              | Use Case                   | Get Key                                            |
| :-------------------- | :------------------------- | :------------------------------------------------- |
| **Groq**              | Fast chat (Llama 3.3 70B)  | [groq.com](https://groq.com)                       |
| **Google AI Studio**  | Vision & Gemini models     | [aistudio.google.com](https://aistudio.google.com) |
| **OpenRouter**        | DeepSeek, Claude, etc.     | [openrouter.ai](https://openrouter.ai)             |
| **Ollama** (optional) | Fully local/offline models | [ollama.com](https://ollama.com)                   |

---

## 🏗️ Architecture

```mermaid
graph TD
    Client[React 18 Frontend] <-->|HTTP/SSE/WebSocket| API[FastAPI Backend]

    subgraph "AI Orchestration"
        API --> Router{Smart Router}
        Router -->|Chat/Stream| LLM[Groq / Gemini / OpenRouter]
        Router -->|Code Tasks| Sandbox[Isolated Docker Container]
        Router -->|Voice| TTS[Edge-TTS + Whisper STT]
        Router -->|Documents| RAG[ChromaDB Vector Search]
    end

    subgraph "Persistent Storage"
        API --> DB[(PostgreSQL)]
        API --> Vector[(ChromaDB)]
        API --> Cache[(Redis)]
    end
```

---

## 🛠️ Tech Stack

| Domain           | Technology                              |
| :--------------- | :-------------------------------------- |
| **Frontend**     | React 18, Vite, TypeScript              |
| **Styling**      | Vanilla CSS, Lucide icons               |
| **Backend**      | FastAPI (Python 3.11), Uvicorn          |
| **Database**     | PostgreSQL + SQLAlchemy                 |
| **Vector Store** | ChromaDB + Sentence Transformers        |
| **Cache**        | Redis                                   |
| **TTS**          | Microsoft Edge-TTS (Professional Indic) |
| **STT**          | Faster Whisper (local, offline)         |
| **Sandboxing**   | Docker (isolated container)             |
| **Auth**         | JWT + Google OAuth 2.0 + OTP            |

---

## 🔧 Configuration (`.env`)

```ini
# LLM API Keys
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
OPENROUTER_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://ai:ai_pass@localhost:5432/autoagent
REDIS_URL=redis://localhost:6379/0

# Auth
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=...

# Privacy
ENABLE_PII_SCRUBBING=true
```

---

## 📡 API Documentation

Access the full interactive API docs (Swagger UI) at:

- **`http://localhost:8000/docs`** — InfiChat API v2.0.0

Route groups include: Auth, OAuth, Chat, Voice, RAG, Code Agent, Image, Snippets, Settings, Admin.

---

## 🤝 Contributing

This project is open-source under the **MIT License**.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes
4. Push and open a Pull Request

---

_Built with ❤️ for the Open Source AI Community._
