<div align="center">

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                    INFICHAT — HERO SECTION                     -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<img src="frontend/public/app_name.png" height="80" alt="InfiChat — Self-Hosted Generative AI Platform" />

<br/>

### **The Ultimate Self-Hosted AI Command Center**

*All Your Intelligence. One Unified Platform. Zero Data Leakage.*

<br/>

[![MIT License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Electron](https://img.shields.io/badge/Electron-41-47848F?style=for-the-badge&logo=electron&logoColor=white)](https://www.electronjs.org/)

<br/>

[![Version](https://img.shields.io/badge/Version-2.0.0-10A37F?style=flat-square)](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat)
[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen?style=flat-square)](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat)
[![CI](https://img.shields.io/github/actions/workflow/status/gugulothubhavith/AI-Chatbot-InfiChat/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat/actions)
[![Files](https://img.shields.io/badge/Source_Files-428+-blue?style=flat-square)]()
[![Code Lines](https://img.shields.io/badge/Lines_of_Code-180,000+-purple?style=flat-square)]()

<br/>

<p>
  <a href="#-quick-start">⚡ Quick Start</a> •
  <a href="#-feature-atlas">✨ Features</a> •
  <a href="ARCHITECTURE.md">🏗️ Architecture</a> •
  <a href="#-api-reference">📡 API</a> •
  <a href="#-deployment-guide">🚀 Deploy</a> •
  <a href="#-contributing">🤝 Contribute</a>
</p>

<br/>

</div>

---

> [!WARNING]
> **🚧 Active Development** — InfiChat is continuously evolving with new features, performance optimizations, and architectural refinements. Expect frequent updates and improvements.

> [!CAUTION]
> **🔒 PROPRIETARY INTELLECTUAL PROPERTY NOTICE**
> 
> While InfiChat provides extensive access to its foundational architecture, certain **Core AI Services and Proprietary UI Logic** are strictly classified and intentionally omitted from this public repository.
> 
> **Restricted Modules Include:**
> - **Core AI Engines:** Deep Research, Chain-of-Thought Reasoning (Deep Thinking), Agentic Web Search, and Multi-Agent Code Orchestration.
> - **Proprietary Frontend Components:** Advanced pipeline visualizations and real-time streaming interfaces (`CodeAgent`, `DeepResearchProgress`, `ai-agent-pipeline`, etc.).
> - **Internal Operations:** Migration utilities, debug tooling, and private environment configurations.
> 
> These exclusions guarantee the protection of proprietary algorithms and enterprise trade secrets while maintaining a robust, deployable open-core foundation.

---

## 📑 Table of Contents

<details open>
<summary><strong>Click to expand full navigation</strong></summary>

- [🛡️ Mission Statement](#%EF%B8%8F-mission-statement)
- [✨ Feature Atlas](#-feature-atlas)
  - [💬 Multi-Provider Streaming Chat](#-multi-provider-streaming-chat)
  - [🎙️ Professional Indic Voice AI](#%EF%B8%8F-professional-indic-voice-ai-tts--stt)
  - [📚 RAG — Retrieval-Augmented Generation](#-rag--retrieval-augmented-generation)
  - [🤖 InfiBuild Studio (5-Agent Code Generation)](#-infibuild-studio-5-agent-code-generation)
  - [🧠 Deep Research & Thinking Engines](#-deep-research--thinking-engines)
  - [🔐 Authentication & Security](#-authentication--security)
  - [🎛️ Enterprise Admin Command Center](#%EF%B8%8F-enterprise-admin-command-center)
  - [💳 Subscription & Monetization Engine](#-subscription--monetization-engine)
  - [🖼️ AI Image Generation](#%EF%B8%8F-ai-image-generation)
  - [🖥️ Desktop Application](#%EF%B8%8F-desktop-application-electron)
- [🏗️ System Architecture & Reference](ARCHITECTURE.md)
- [🛠️ Technology Stack](#%EF%B8%8F-technology-stack)
- [📋 Prerequisites](#-prerequisites)
- [⚡ Quick Start](#-quick-start)
- [🔧 Manual Setup Guide](#-manual-setup-guide)
- [🗝️ API Keys & Configuration](#%EF%B8%8F-api-keys--configuration)
- [📁 Monorepo Architecture](#-monorepo-architecture--project-structure)
- [📡 API Reference](#-api-reference)
- [🔐 Defense-in-Depth Security Model](#-defense-in-depth-security-model)
- [🚀 Deployment Guide](#-deployment-guide)
- [🐛 Troubleshooting Guide](#-troubleshooting-guide)
- [📊 Performance Benchmarks](#-performance-benchmarks)
- [🗺️ Roadmap](#%EF%B8%8F-roadmap)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [🙏 Acknowledgements](#-acknowledgements)
- [📞 Contact](#-contact)

</details>

---

## 🛡️ Mission Statement

<div align="center">

**InfiChat was engineered on a single foundational principle:**

### *Unify the world's best AI models into one sovereign command center — entirely under your control.*

</div>

<br/>

Instead of fragmenting your workflow across ChatGPT, Claude, Gemini, and specialized coding tools, InfiChat provides a **single, self-hosted intelligence gateway** that dynamically routes every request to the optimal AI provider — whether that's **Groq** for lightning-fast inference, **Google Gemini** for multimodal vision, **NVIDIA NIM** for enterprise-grade autonomous coding, or **DuckDuckGo + Arxiv** for deep research synthesis.

**Every byte of data stays on your infrastructure. No telemetry. No analytics. No compromise.**

<br/>

| Capability | Standard Chatbots | **InfiChat** |
|:---|:---:|:---:|
| Multi-Provider Dynamic LLM Routing (Groq, Gemini, OpenRouter, Ollama) | ❌ | ✅ |
| InfiBuild Studio (5-Agent Autonomous Code Generation) | ❌ | ✅ |
| Deep Research & Extended Thinking Modes | ❌ | ✅ |
| Professional Indic Voice AI (TTS + STT, 4 neural voices) | ❌ | ✅ |
| RAG with Local Vector Embeddings (ChromaDB + FAISS) | ❌ | ✅ |
| AI Image Generation (Pollinations / Stable Diffusion XL) | ❌ | ✅ |
| Enterprise Admin Command Center (25 governance modules) | ❌ | ✅ |
| Subscription, Usage Metering & Feature Gating | ❌ | ✅ |
| Native Desktop Application (Electron — Win/Mac/Linux) | ❌ | ✅ |
| Self-Hosted — Zero Data Leaves Your Infrastructure | ❌ | ✅ |
| Defense-in-Depth Security (6-layer model, RBAC, AI Firewall) | ❌ | ✅ |
| Real-time WebSocket Streaming & Live Code Execution | ❌ | ✅ |

> **InfiChat is a production-ready, enterprise-grade AI gateway for professionals who demand ChatGPT-level UX — powered by the best APIs on the market — fully self-hosted, fully sovereign.**

---

## ✨ Feature Atlas

### 💬 Multi-Provider Streaming Chat

InfiChat's **Smart Router** (`llm_router.py` — 20,630 bytes of routing intelligence) dynamically selects the optimal LLM provider based on task type, model availability, latency requirements, and cost efficiency.

| Provider | Model | Speed | Primary Use Case |
|:---|:---|:---:|:---|
| **Groq** | Llama 3.3 70B Versatile | ~300 tok/s | General chat, summarization, reasoning |
| **NVIDIA NIM** | StarCoder2 7B / GLM 5.2 | Ultra-fast | InfiBuild Studio autonomous coding |
| **Google Gemini** | Flash 2.0 | Ultra-fast | Vision, multimodal, long-context documents |
| **OpenRouter** | DeepSeek V3, Claude 3.5, 100+ models | Varies | Specialized cognitive tasks |
| **Ollama** | Any local model (Mistral, Phi, etc.) | Hardware-dependent | 100% offline private inference |

**Core Chat Capabilities:**

- 🔄 **Real-time SSE streaming** — Token-by-token output via Server-Sent Events with `useChatStream.ts` hook
- 💾 **Persistent multi-turn history** — Conversation sessions with PostgreSQL-backed archival
- 🔗 **Shareable conversation links** — Access-controlled public URLs with expiry controls
- 🛡️ **PII scrubbing** — Automatic redaction of personally identifiable information via `privacy_service.py`
- 📊 **Token usage tracking** — Per-message and per-session metering with visual `TokenUsageBadge.tsx`
- 🎨 **Accent color theming** — User-customizable interface colors via `useAccentColor.ts`
- ⌨️ **Command palette** (`⌘K`) — Instant navigation and action shortcuts via `CommandPalette.tsx` (powered by `cmdk`)
- 🌗 **Dark/Light themes** — System-aware theme switching with `ThemeContext.tsx` and smooth CSS transitions

---

### 🎙️ Professional Indic Voice AI (TTS / STT)

InfiChat features a **best-in-class voice pipeline** tailored for multilingual Indian users, with a dedicated standalone **Voice AI Agent** module (`TTS and STT/` — 30 source files, fully independent deployment).

#### Text-to-Speech (TTS) — Neural Voice Profiles

| Profile | Locale | Voice Engine | Character |
|:---|:---|:---|:---|
| 🔊 **Professional English** | `en-IN` | `PrabhatNeural` | Authoritative, broadcast-quality |
| 🔊 **Corporate Hindi** | `hi-IN` | `SwaraNeural` | Warm, professional female |
| 🔊 **Empathetic Telugu** | `te-IN` | `MohanNeural` | Calm, reassuring male |
| 🔊 **Alert Hindi (Fast)** | `hi-IN` | `Swara` | Rapid, notification-style |

**Voice Configuration** (`voice_config.json` — 1,342 bytes of persona engineering):

| Parameter | Description |
|:---|:---|
| **Persona Tuning** | Tone, energy, confidence, warmth controls |
| **Delivery Parameters** | Speaking speed, clarity, pause models (comma: 180ms, full-stop: 320ms) |
| **Pronunciation Rules** | Abbreviation expansion (AI → "A I", OTP → "O T P"), year styles, technical term mode |
| **Dialogue Rules** | Polite acknowledgement, no Western slang, empathetic error tones |
| **Response Framework** | Acknowledge → State action → Give result → Offer next help |

**Technical Highlights:**

- ⚡ **Sub-1-second audio latency** — MP3 streaming starts before synthesis completes
- 🇮🇳 **Native Indian number formatting** — Correctly reads ₹ Lakhs, Crores, and common abbreviations via `tts_formatter.py`
- ⏸️ **Voice interruption** — User can stop playback mid-sentence
- 📡 **Streaming audio chunks** — Progressive delivery over WebSocket

#### Speech-to-Text (STT) — Offline-First

| Attribute | Detail |
|:---|:---|
| **Engine** | Faster Whisper (CTranslate2-optimized inference) |
| **Privacy** | **100% offline** — voice data never leaves your machine |
| **Languages** | Multilingual transcription across Indian and global languages |
| **UI** | Real-time waveform visualization in the browser |
| **Models** | Configurable: `tiny`, `base`, `small`, `medium`, `large-v3` |

---

### 📚 RAG — Retrieval-Augmented Generation

Transform static documents into an interactive, AI-powered knowledge base with intelligent retrieval and citation-grounded responses.

**Pipeline Architecture:**

```
📄 Document Upload → Parse → Chunk → Embed → Index → Query → Retrieve → Augment → Generate
```

| Stage | Implementation | Details |
|:---|:---|:---|
| **Upload** | `rag.py` API route | PDF, DOCX, TXT, HTML, Web URL |
| **Parse** | `pypdf` + `pdfplumber` + `python-docx` + `beautifulsoup4` + `trafilatura` | Multi-format extraction with layout preservation |
| **Chunk** | Recursive character-aware splitter | 512-token windows, 64-token overlap |
| **Embed** | `sentence-transformers` (`all-MiniLM-L6-v2`) | 384-dimensional vectors, ~80MB model, runs locally |
| **Index** | ChromaDB (production) / FAISS (local dev) | Persistent vector storage on local disk |
| **Retrieve** | Cosine similarity search | Top-k = 5 context injection |
| **Generate** | LLM with injected context | Citation-grounded responses via `rag_service.py` (16,902 bytes) |

**Supported Document Formats:**

| Format | Parser(s) | Max Size |
|:---|:---|:---:|
| PDF | `pypdf` + `pdfplumber` | 50 MB |
| DOCX | `python-docx` | 50 MB |
| TXT | Python built-in | 50 MB |
| HTML | `beautifulsoup4` | 50 MB |
| Web URL | `trafilatura` | — |

---

### 🤖 Multi-Agent Sandboxed Code Execution

InfiChat employs an advanced **Multi-Agent Code Orchestrator** (`code_orchestrator/` — 3 core files, 33,683 bytes of orchestration logic) powered by NVIDIA NIM to autonomously plan, write, review, and execute code.

**Agent Pipeline:**

```
User Request → 🧠 Planner → 💻 Coder → 🔍 Reviewer → ✅ Orchestrator → 💻 Local Subprocess Sandbox → 📺 Live Output
```

| Agent | Model | Responsibility |
|:---|:---|:---|
| **🧠 Planner** | Llama 3.3 (via Groq) | Decomposes complex tasks into actionable steps |
| **💻 Coder** | NVIDIA StarCoder2 / GLM 5.2 | Generates enterprise-quality code |
| **🔍 Reviewer** | NVIDIA StarCoder2 / GLM 5.2 | Audits code for bugs, security, and correctness |
| **✅ Orchestrator** | `orchestrator.py` (14,467 bytes) | Coordinates pipeline, handles retries, validates output |

**Sandbox Security:**

| Control | Implementation |
|:---|:---|
| **Isolation** | Zero-Trust AST Validator — blocks dangerous operations prior to local execution |
| **Live Streaming** | Real-time stdout/stderr via WebSocket (`ws_code.py`) |
| **Auto-Debugging** | Agent reads runtime errors → self-corrects → re-executes |
| **CPU Limit** | 50% CPU cap (`cpu_quota=50000`) |
| **Memory Limit** | 256MB hard limit |
| **Network** | Completely disabled — no external access |
| **Lifecycle** | Ephemeral — container destroyed after each session |
| **Image** | `python:3.11-slim` — minimal attack surface |

---

### 🧠 Deep Research & Thinking Engines

Two advanced cognitive processing modes for complex intellectual tasks:

#### 🔬 Deep Research (`deep_research/` — 3 core files + agents + utils)

An autonomous multi-agent research pipeline that synthesizes information from multiple sources:

```
Query → 🔑 Keyword Extraction (YAKE + SpaCy NER) → 🌐 Parallel Search Dispatch
                                                        ├── DuckDuckGo (web)
                                                        └── Arxiv (academic papers)
                                                    → 📄 Content Extraction (trafilatura + Arxiv API)
                                                    → 🧠 Multi-Source Synthesis (LLM aggregation)
                                                    → 📡 Streaming Response with Citations
```

- **Real-time progress** streamed to `DeepResearchProgress.tsx` (7,561 bytes)
- **Academic integration** via Arxiv API for peer-reviewed papers
- **NLP-powered** keyword extraction using YAKE and SpaCy

#### 🤔 Deep Thinking (`deep_thinking/` — 3 core files + agents)

Extended chain-of-thought reasoning for complex problems:

```
Complex Problem → 📋 Decomposition → 🔄 Iterative Thinking Steps
                                        ├── Hypothesis generation
                                        ├── Evidence gathering
                                        ├── Reasoning validation
                                        └── Conclusion synthesis
                                     → 📺 Real-time Step Streaming → Final Synthesized Answer
```

- **Streaming reasoning chain** via `DeepThinkingProgress.tsx` (14,265 bytes)
- **Configurable depth** and iteration limits
- **Visual progress indicators** for each thinking step

---

### 🔐 Authentication & Security

Enterprise-grade identity and access management system:

| Feature | Implementation |
|:---|:---|
| **Email + OTP** | Two-factor authentication (TOTP-compatible) via `email_service.py` (20,665 bytes) |
| **Google OAuth 2.0** | Single sign-on — one-click login via `oauth.py` |
| **JWT Sessions** | Configurable access tokens (60min) + refresh tokens (30d) via `security.py` |
| **Password Hashing** | Bcrypt with cost factor 12 (`passlib[bcrypt]`) |
| **Rate Limiting** | Per-route configurable via `slowapi` |
| **RBAC** | User, Admin, Super-Admin roles via `rbac.py` (2,761 bytes) |
| **CSRF Protection** | Middleware on all state-changing requests via `csrf.py` |
| **Input Sanitization** | XSS prevention via `bleach` + custom `input_sanitizer.py` (5,504 bytes) |
| **AI Firewall** | Prompt injection detection and blocking via `ai_firewall.py` |
| **Audit Logging** | Tamper-proof trail of all critical actions via `audit_logging.py` |
| **PII Scrubbing** | Auto-redacts emails, phones, names from logs via `privacy_service.py` |
| **Sensitive Log Masking** | `RedactingFilter` in `main.py` redacts passwords, tokens, keys from all log output |

---

### 🎛️ Enterprise Admin Command Center

A comprehensive, real-time governance dashboard with **25 specialized modules** — built with React 18, Three.js, Recharts, React Flow, XTerm.js, and React Globe:

| Category | Module | Key Technologies | File Size |
|:---|:---|:---|:---:|
| **📊 Monitoring** | Dashboard | Recharts, psutil telemetry | — |
| | Analytics | Trend visualization, data insights | 7.3 KB |
| | Telemetry | Observability metrics | 8.7 KB |
| | Usage Monitoring | Real-time API tracking, quotas | 9.8 KB |
| **🏗️ Infrastructure** | Hardware/GPU | GPU metrics, resource allocation | 6.9 KB |
| | Topology Map | Three.js infrastructure visualization | 7.7 KB |
| | Cluster Federation | Multi-node cluster management | 8.6 KB |
| | Predictive Scaling | AI-driven resource recommendations | 7.7 KB |
| **🔒 Security** | Network Security | Firewall rules, threat detection | 20.4 KB |
| | DEFCON Controls | Emergency security posture escalation | 12.4 KB |
| | Prompt Firewall | AI safety rules, injection prevention | 9.1 KB |
| | RBAC Studio | Role & permission management | 8.9 KB |
| **💾 Data** | Database Control | PostgreSQL, Redis, ChromaDB introspection | 18.1 KB |
| | Knowledge Graph | React Force Graph 3D visualization | 9.9 KB |
| **⚙️ Operations** | Release Management | Deployment history, rollback, versioning | 42.4 KB |
| | Auto Healing | Self-healing infrastructure automation | 10.1 KB |
| | Chaos Monkey | Resilience testing via controlled failures | 14.4 KB |
| | Platform Outage | Incident management, status page | 19.4 KB |
| **💼 Business** | Subscription Plans | Plan CRUD, pricing tiers, feature gates | 23.3 KB |
| | User Plan Manager | Per-user plan assignment, upgrade/downgrade | 17.6 KB |
| | Tenant Manager | Multi-tenancy isolation | 7.6 KB |
| **🔧 Platform** | Model Hub | LLM model registry, routing config | 13.3 KB |
| | Developer Keys | API key generation, rotation, revocation | 9.3 KB |
| | Global Broadcast | System-wide announcements | 18.5 KB |
| | Platform Branding | White-label customization | 9.5 KB |
| | Workflow Orchestrator | Visual pipeline builder (React Flow) | 13.0 KB |

---

### 💳 Subscription & Monetization Engine

Full-featured SaaS-ready subscription system:

- **Tiered plans** with configurable feature gates (message limits, model access, storage quotas)
- **Usage metering** — per-user token counting and API call tracking via `subscription_service.py` (11,576 bytes)
- **Seed automation** — default plans bootstrapped on first launch via `seed_plans.py` (5,400 bytes)
- **Frontend enforcement** — automatic `SubscriptionGate.tsx` (10,588 bytes) modal when limits are reached
- **Admin management** — create, edit, assign plans via the Command Center

---

### 🖼️ AI Image Generation

- AI-powered image generation via **Pollinations API** or locally hosted **Stable Diffusion XL**
- Prompt-to-image directly within the chat interface
- Gallery view with download support
- Dedicated `ImageGen.tsx` page (8,982 bytes) with full generation controls
- Backend orchestration via `image_service.py` (4,478 bytes)

---

### 🖥️ Desktop Application (Electron)

InfiChat ships as a native desktop application:

| Attribute | Detail |
|:---|:---|
| **Runtime** | Electron 41 with secure preload scripts |
| **Platforms** | Windows (`.exe` portable), macOS (`.dmg`), Linux (`.AppImage`) |
| **Build System** | `electron-builder` with NSIS installer support |
| **Security** | Custom `preload.js` context bridge — no `nodeIntegration` |
| **App ID** | `com.infichat.app` |
| **Main Process** | `electron/main.js` (4,339 bytes) — window management, IPC |
| **Build Script** | `build_win.ps1` for Windows-specific builds |

**Build Commands:**

```bash
npm run build:win      # Windows (.exe portable)
npm run build:mac      # macOS (.dmg)
npm run build:linux    # Linux (.AppImage)
```

---

## 🏗️ System Architecture

> [!NOTE]
> The comprehensive system architecture, multi-agent engine diagrams, and technical module references have been moved to [ARCHITECTURE.md](ARCHITECTURE.md) to keep this guide focused on deployment and usage.

## 🛠️ Technology Stack

### Frontend — Main User Interface

| Technology | Version | Role | Key File(s) |
|:---|:---:|:---|:---|
| React | 18 | UI framework with hooks-based architecture | `App.tsx` (20,471 bytes) |
| TypeScript | 5.x | Type-safe component development | `tsconfig.json` |
| Vite | 5.x | Lightning-fast HMR dev server & bundler | `vite.config.ts` |
| Tailwind CSS | 3.4 | Utility-first responsive styling | `tailwind.config.js` (6,246 bytes) |
| Framer Motion | 11.x | Declarative animations and transitions | — |
| GSAP | 3.15 | High-performance scroll/timeline animations | — |
| Radix UI | Latest | 15 accessible headless component primitives | `@radix-ui/*` |
| Monaco Editor | 0.55 | VS Code-grade in-browser code editor | `@monaco-editor/react` |
| Zustand | 4.5 | Lightweight global state management | — |
| React Query | 5.x | Server state management and caching | `@tanstack/react-query` |
| React Router | 6.x | Client-side routing and navigation | `react-router-dom` |
| Sonner | 2.x | Toast notification system | — |
| cmdk | 1.x | Command palette (⌘K) component | `CommandPalette.tsx` |
| Electron | 41.x | Native desktop application shell | `electron/main.js` |

### Frontend — Admin Command Center

| Technology | Version | Role |
|:---|:---:|:---|
| React | 18 | UI framework |
| Tailwind CSS | 4.2 | Styling (v4 with `@tailwindcss/vite` plugin) |
| Recharts | 3.7 | Data visualization and charting |
| React Flow | 12.x | Node-based graph/workflow visualization |
| React Three Fiber | 9.x | 3D WebGL rendering (topology, globe) |
| Three.js | 0.183 | 3D graphics engine |
| React Globe.gl | 2.37 | Geographic data globe visualization |
| React Force Graph 3D | 1.29 | 3D force-directed graph (knowledge graph) |
| XTerm.js | 6.0 | Terminal emulator (in-browser shell) |
| Framer Motion | 12.x | Advanced UI animations |
| Lucide React | Latest | Consistent icon library |
| XLSX | 0.18 | Excel file export capability |

### Backend — API & Intelligence Layer

| Technology | Version | Role | File Size |
|:---|:---:|:---|:---:|
| FastAPI | 0.109.2 | Async REST API + WebSocket server | `main.py` (16,288 bytes) |
| Uvicorn | 0.27.1 | ASGI server with lifespan management | — |
| Pydantic | 2.6.1 | Data validation and settings management | `config.py` (5,061 bytes) |
| SQLAlchemy | 2.0.25 | Async ORM with connection pooling | 24 model files |
| Alembic | 1.13.1 | Database migrations and schema versioning | — |
| python-jose | 3.3.0 | JWT token generation and validation | `security.py` (6,933 bytes) |
| passlib/bcrypt | 1.7.4 | Secure password hashing (cost factor 12) | — |
| SlowAPI | 0.1.9 | Request rate limiting | — |
| httpx | 0.26.0 | Async HTTP client for external API calls | — |
| bleach | 6.1+ | HTML sanitization for XSS prevention | `input_sanitizer.py` |
| cryptography | 42.0+ | Encryption primitives and key management | `encryption.py` |
| psutil | 5.9.8 | System resource monitoring (CPU, RAM) | — |
| Prometheus Client | 0.20.0 | Metrics export for observability | `metrics.py` |

### AI & Machine Learning

| Technology | Role |
|:---|:---|
| Groq SDK | Ultra-fast Llama 3.3 70B inference |
| Google Generative AI | Gemini Flash 2.0 multimodal |
| OpenRouter | Gateway to 100+ LLM models |
| NVIDIA NIM | Enterprise multi-agent code generation |
| ChromaDB ≥0.4.22 | Production vector database for RAG |
| FAISS (CPU) ≥1.7.4 | Lightweight local vector search |
| sentence-transformers ≥2.2 | Document embedding (`all-MiniLM-L6-v2`) |
| faster-whisper ≥0.10.0 | CTranslate2-based local STT |
| edge-tts ≥6.1.9 | Microsoft Neural Indic TTS |
| SpaCy ≥3.7.0 | NLP pipeline for entity/keyword extraction |
| YAKE ≥0.4.8 | Unsupervised keyword extraction |
| DuckDuckGo Search ≥5.0 | Web search for deep research |
| Arxiv ≥2.1.0 | Academic paper search and retrieval |
| tiktoken ≥0.6.0 | Accurate token counting |
| Pillow ≥10.0.0 | Image processing and manipulation |

### Document Parsing

| Technology | Role |
|:---|:---|
| pypdf ≥4.0.0 | PDF text extraction |
| pdfplumber ≥0.10.0 | Advanced PDF parsing with layout preservation |
| python-docx ≥1.1.0 | Microsoft Word document parsing |
| beautifulsoup4 ≥4.12 | HTML/XML parsing for web content |
| trafilatura ≥1.6.0 | Web page content extraction and cleaning |

### Infrastructure

| Technology | Role |
|:---|:---|
| PostgreSQL 16 | Primary relational database (users, chats, plans, orgs) |
| Redis 7 | Session caching, pub/sub, rate limit counters |
| asyncpg | High-performance async PostgreSQL driver |
| aiosqlite | Async SQLite driver for local development |
| pip-audit | Dependency vulnerability scanning |

---

## 📋 Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|:---|:---:|:---:|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16 GB+ |
| **Storage** | 20 GB | 50 GB+ |
| **OS** | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04+ |
| **GPU** | Not required | NVIDIA RTX (for Ollama + Whisper acceleration) |

### Required Software

| Software | Version | Download |
|:---|:---:|:---|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 20+ | [nodejs.org](https://nodejs.org) |
| **Git** | Latest | [git-scm.com](https://git-scm.com) |

### Optional Software

| Software | Purpose | Download |
|:---|:---|:---|
| **Ollama** | 100% offline local LLM inference | [ollama.com](https://ollama.com) |
| **NVIDIA GPU Drivers** | Whisper acceleration + local model inference | [nvidia.com](https://www.nvidia.com/drivers) |

---

## ⚡ Quick Start

The fastest way to get InfiChat running — one script does everything.

```powershell
# 1. Clone the repository
git clone https://github.com/gugulothubhavith/AI-Chatbot-InfiChat.git
cd AI-Chatbot-InfiChat

# 2. Run the automated setup script
.\setup_windows.ps1
```

**The `setup_windows.ps1` script automatically:**

1. ✅ Verifies Python 3.11+ and Node.js are installed
2. ✅ Prompts for API keys and writes your `.env` file
3. ✅ Creates a Python virtual environment and installs all 83 dependencies
4. ✅ Initializes the PostgreSQL database schema
5. ✅ Builds and launches all services
6. ✅ Opens the application at **`http://localhost:5173`**

> [!TIP]

---

## 🔧 Manual Setup Guide

For advanced users, custom deployments, or Linux/macOS systems:

### Step 1: Clone & Configure

```bash
git clone https://github.com/gugulothubhavith/AI-Chatbot-InfiChat.git
cd AI-Chatbot-InfiChat

# Copy environment template
cp backend/.env.example backend/.env
# Edit .env with your API keys (see Configuration section below)
```

### Step 2: Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Linux/macOS

# Install all Python dependencies (74 packages)
pip install -r requirements.txt

# Initialize the database (ensure PostgreSQL is running)
python fix_db_schema.py
```

### Step 3: Frontend Setup

```bash
# Main frontend
cd frontend
npm install

# Admin dashboard (separate terminal)
cd admin-frontend
npm install
```

### Step 4: Start All Services

<details>
<summary><strong>Option A — Monorepo Launcher (Recommended)</strong></summary>

```bash
# Install root dependencies first
npm install

# Start ALL services concurrently (Backend + Frontend + Admin)
npm run dev

# Or start only the UI layer (Frontend + Admin)
npm run dev:ui
```

Uses `concurrently` to orchestrate all three services with color-coded output.

</details>

<details>
<summary><strong>Option B — Batch Launcher (Windows)</strong></summary>

```batch
.\start_all.bat
```

</details>

<details>
<summary><strong>Option C — Manual (3 Terminals)</strong></summary>

```bash
# Terminal 1: FastAPI Backend
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2: React Frontend
cd frontend
npm run dev

# Terminal 3: Admin Dashboard
cd admin-frontend
npm run dev
```

</details>


### Step 5: Access the Application

| Service | URL | Description |
|:---|:---|:---|
| **Frontend UI** | http://localhost:5173 | Main chat interface |
| **Admin Dashboard** | http://localhost:5174 | Enterprise command center |
| **Backend API** | http://localhost:8080 | FastAPI REST API |
| **Swagger Docs** | http://localhost:8080/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8080/redoc | Alternative API reference |

---

## 🗝️ API Keys & Configuration

### Required API Keys (All have free tiers)

| Provider | Purpose | Free Tier | Sign Up |
|:---|:---|:---:|:---|
| **Groq** | Llama 3.3 70B — primary fast chat | ✅ Yes | [console.groq.com](https://console.groq.com) |
| **Google AI Studio** | Gemini Flash — vision & multimodal | ✅ Yes | [aistudio.google.com](https://aistudio.google.com) |
| **OpenRouter** | DeepSeek, Claude, 100+ models | ✅ Yes | [openrouter.ai](https://openrouter.ai) |

### Optional Configuration

| Provider | Purpose | Sign Up |
|:---|:---|:---|
| **Ollama** | 100% offline local models | [ollama.com](https://ollama.com) |
| **Google OAuth** | Google SSO login | [console.cloud.google.com](https://console.cloud.google.com) |
| **NVIDIA NIM** | Enterprise code agent models | [build.nvidia.com](https://build.nvidia.com) |

### Complete `.env` Configuration Reference

<details>
<summary><strong>Click to expand full .env template</strong></summary>

```ini
# ═══════════════════════════════════════════════════════════════
#  InfiChat — Environment Configuration
#  Copy this file to backend/.env and fill in your values
# ═══════════════════════════════════════════════════════════════

# ─── LLM API Keys ─────────────────────────────────────────────
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─── Database Configuration ───────────────────────────────────
DATABASE_URL=postgresql://ai:ai_pass@localhost:5432/autoagent
# DATABASE_URL=sqlite:///./data/infichat.db
REDIS_URL=redis://localhost:6379/0

# ─── Authentication & Security ────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-256-bit-random-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# ─── Google OAuth 2.0 (Optional) ─────────────────────────────
GOOGLE_CLIENT_ID=xxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8080/api/oauth/google/callback

# ─── NVIDIA NIM & Multi-Agent Keys (Optional) ────────────────
CODER_API_KEY=nvapi-...
REVIEWER_API_KEY=nvapi-...
PLANNER_API_KEY=nvapi-...
CODER_MODEL=z-ai/glm-5.2
PLANNER_MODEL=z-ai/glm-5.2

# ─── Email Settings (Optional — for OTP) ─────────────────────
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here

# ─── Feature Flags ────────────────────────────────────────────
ENABLE_PII_SCRUBBING=true
ENABLE_RATE_LIMITING=true
ENABLE_CODE_SANDBOX=true
MAX_UPLOAD_SIZE_MB=50

# ─── Application Settings ────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

</details>

---

## 📁 Monorepo Architecture — Project Structure

InfiChat is engineered as a **true enterprise monorepo** spanning 4 application layers, 25 admin modules, and **428+ source files** of custom logic.

<details open>
<summary><strong>🗺️ Complete Directory Tree</strong></summary>

> [!CAUTION]
> **🔒 SPECIFIC PROPRIETARY SCRIPTS & SECRETS:** Internal testing, migration, and proprietary utility scripts (e.g., `fix_*.py`, `migrate_*.py`, `test_*.py`), Core AI Services (`backend/app/services/deep_research/`, `backend/app/services/deep_thinking/`, `backend/app/services/web_search/`, `backend/app/services/code_orchestrator/`, `backend/app/services/code_agent.py`), and Proprietary Frontend Components (`frontend/src/pages/CodeAgent.tsx`, `frontend/src/components/ui/ai-agent-pipeline.tsx`, `frontend/src/components/DeepResearchProgress.tsx`, `frontend/src/components/DeepThinkingProgress.tsx`, `frontend/src/components/WebSearchProgress.tsx`, `frontend/src/hooks/useWebSearchStream.ts`) are intentionally hidden from this public documentation to protect proprietary intellectual property.

```text
AI-Chatbot-InfiChat/
│
├── 🐍 backend/                              ══ Core Intelligence & API Gateway ══
│   │
│   ├── app/
│   │   ├── main.py                          # Application entrypoint (16,288 bytes)
│   │   │                                    # Lifespan hooks, CORS, model preloading, RedactingFilter
│   │   ├── __init__.py
│   │   │
│   │   ├── api/                             # ══ 24 Route Controllers ══
│   │   │   ├── auth.py                      # Registration, login, logout, password reset, OTP
│   │   │   ├── oauth.py                     # Google OAuth 2.0 flow
│   │   │   ├── chat.py                      # LLM streaming chat, history, shared links
│   │   │   ├── voice.py                     # TTS synthesis, STT transcription
│   │   │   ├── rag.py                       # Document upload, knowledge base query
│   │   │   ├── code_agent.py                # Sandboxed Python execution trigger
│   │   │   ├── image.py                     # AI image generation
│   │   │   ├── research.py                  # Deep research mode endpoints
│   │   │   ├── thinking.py                  # Deep thinking mode endpoints
│   │   │   ├── snippets.py                  # Code snippet CRUD
│   │   │   ├── settings.py                  # User preferences and profile
│   │   │   ├── admin.py                     # User management, system stats
│   │   │   ├── admin_governance.py          # Governance policies, compliance
│   │   │   ├── admin_security.py            # Security config, key rotation
│   │   │   ├── admin_zero_trust.py          # Zero-trust security posture
│   │   │   ├── subscriptions.py             # Subscription plan management
│   │   │   ├── organizations.py             # Multi-tenant org management
│   │   │   ├── system.py                    # System health, metrics, diagnostics
│   │   │   ├── metrics.py                   # Prometheus metrics export
│   │   │   ├── proxy.py                     # API proxy endpoints
│   │   │   ├── ws_agent.py                  # WebSocket: agent communication
│   │   │   ├── ws_broadcast.py              # WebSocket: real-time broadcast
│   │   │   └── ws_code.py                   # WebSocket: live code execution
│   │   │
│   │   ├── services/                        # ══ Business Logic Layer (18 services) ══
│   │   │   ├── llm_router.py                # 🧠 Smart LLM Router
│   │   │   ├── chat_service.py              # Chat session management
│   │   │   ├── voice_service.py             # Voice pipeline: TTS + STT
│   │   │   ├── indic_voice_service.py       # Indian language specialization
│   │   │   ├── rag_service.py               # RAG: embed, store, retrieve
│   │   │   ├── sandbox_service.py           # Local subprocess sandbox lifecycle
│   │   │   ├── image_service.py             # Image generation orchestration
│   │   │   ├── email_service.py             # Transactional email & OTP
│   │   │   ├── agent_service.py             # Agent task coordination
│   │   │   ├── ai_orchestrator.py           # High-level AI orchestration
│   │   │   ├── ai_firewall.py               # Prompt safety & injection prevention
│   │   │   ├── memory_service.py            # Conversation memory management
│   │   │   ├── privacy_service.py           # PII detection & scrubbing
│   │   │   ├── data_retention.py            # Data lifecycle & cleanup
│   │   │   ├── self_healing.py              # Self-healing infrastructure
│   │   │   ├── subscription_service.py      # Plan management & billing
│   │   │   ├── seed_admin.py                # Default admin user seeding
│   │   │   ├── seed_plans.py                # Default plan seeding
│   │   │
│   │   ├── core/                            # ══ Security & Configuration Layer ══
│   │   │   ├── config.py                    # Pydantic Settings — all env vars
│   │   │   ├── security.py                  # JWT signing, token validation
│   │   │   ├── auth.py                      # Authentication utilities
│   │   │   ├── rbac.py                      # Role-Based Access Control
│   │   │   ├── encryption.py                # Field-level encryption
│   │   │   ├── redis_client.py              # Async Redis connection
│   │   │   ├── deps.py                      # FastAPI dependency injection
│   │   │   ├── compat.py                    # Cross-database compatibility
│   │   │   └── json_utils.py                # JSON serialization utils
│   │   │
│   │   ├── middleware/                      # ══ Request Processing Pipeline ══
│   │   │   ├── audit_logging.py             # Tamper-proof action logging
│   │   │   ├── csrf.py                      # CSRF protection
│   │   │   ├── firewall.py                  # Application-level firewall
│   │   │   ├── input_sanitizer.py           # XSS prevention & cleaning
│   │   │   ├── tenant.py                    # Multi-tenancy isolation
│   │   │   └── usage_tracker.py             # Per-request usage metering
│   │   │
│   │   ├── models/                          # ══ SQLAlchemy ORM Layer (24 models) ══
│   │   │   ├── __init__.py                  # Model registry
│   │   │   ├── user.py                      # User, profile, preferences
│   │   │   ├── chat.py                      # Chat sessions, messages
│   │   │   ├── admin.py                     # Admin entities
│   │   │   ├── subscription.py              # Plans, tiers, limits
│   │   │   ├── security.py                  # Security events, keys
│   │   │   ├── organization.py              # Multi-tenant orgs
│   │   │   ├── workspace.py                 # Workspace model
│   │   │   ├── incidents.py                 # Incident management
│   │   │   ├── observability.py             # Metrics, telemetry
│   │   │   ├── plugins.py                   # Plugin system
│   │   │   ├── otp.py                       # OTP records
│   │   │   ├── memory.py                    # Conversation memory
│   │   │   ├── file.py                      # File uploads
│   │   │   ├── snippets.py                  # Code snippets
│   │   │   ├── ai_model.py                  # AI model registry
│   │   │   ├── rag_analytics.py             # RAG metrics
│   │   │   ├── data_governance.py           # Data governance
│   │   │   ├── business_intelligence.py     # BI entities
│   │   │   ├── system.py                    # System config
│   │   │   ├── types.py                     # Custom column types
│   │   │   ├── utils.py                     # Model utilities
│   │   │   ├── kokoro_setup.py              # Kokoro TTS setup
│   │   │   └── vits_setup.py                # VITS TTS setup
│   │   │
│   │   ├── schemas/                         # ══ Pydantic v2 Validation Schemas ══
│   │   │   ├── auth.py, chat.py, user.py, voice.py, code.py
│   │   │   └── admin_governance.py, admin_security.py
│   │   │
│   │   ├── database/                        # ══ Database Connection Layer ══
│   │   │   └── db.py                        # Async engine, session factory, init_db
│   │   │
│   │   └── static/                          # Backend static assets
│   │
│   ├── requirements.txt                     # Python dependencies (74 packages)
│   ├── alembic.ini                          # Migration configuration
│   └── .env.example                         # Environment variable template
│
├── ⚛️  frontend/                             ══ Primary User Interface ══
│   │
│   ├── src/
│   │   ├── App.tsx                          # Root application with routing
│   │   ├── main.tsx                         # React DOM render entrypoint
│   │   │
│   │   ├── components/                      # ── 26 Reusable UI Components ──
│   │   │   ├── ChatInput.tsx                # Message input with voice, attachments
│   │   │   ├── ChatMessage.tsx              # Message bubble with markdown
│   │   │   ├── Sidebar.tsx                  # Navigation sidebar
│   │   │   ├── SettingsModal.tsx            # Comprehensive settings panel
│   │   │   ├── CommandPalette.tsx           # ⌘K quick-action launcher
│   │   │   ├── AgentTaskPlan.tsx            # Multi-agent visualization
│   │   │   ├── TokenUsageBadge.tsx          # Token consumption display
│   │   │   ├── SubscriptionGate.tsx         # Plan enforcement modal
│   │   │   ├── ErrorBoundary.tsx            # Error boundary wrapper
│   │   │   ├── Logo.tsx, ProfileAvatar.tsx, ScrollProvider.tsx
│   │   │   ├── settings/                    # Settings sub-components (5 files)
│   │   │   ├── sidebar/                     # Sidebar sub-components (2 files)
│   │   │   └── ui/                          # Primitives: Button, Card, Input, Switch, Toast,
│   │   │                                    # ConfirmDialog, Skeleton, TypingIndicator
│   │   │
│   │   ├── pages/                           # ── 8 Top-Level Route Views ──
│   │   │   ├── Chat.tsx                     # Main chat interface
│   │   │   ├── ImageGen.tsx                 # AI image generation
│   │   │   ├── RAG.tsx                      # Knowledge base management
│   │   │   ├── Snippets.tsx                 # Code snippet manager
│   │   │   ├── Login.tsx                    # Authentication page
│   │   │   ├── Register.tsx                 # Registration page
│   │   │   ├── SharedChatView.tsx           # Public shared chat viewer
│   │   │   └── Admin.tsx                    # Admin redirect
│   │   │
│   │   ├── hooks/                           # ── 5 Custom React Hooks ──
│   │   │   ├── useAuth.tsx                  # Authentication state & guards
│   │   │   ├── useChatStream.ts             # SSE streaming chat
│   │   │   ├── useResearchStream.ts         # Deep research streaming
│   │   │   ├── useThinkingStream.ts         # Deep thinking streaming
│   │   │   └── useAccentColor.ts            # Theme accent color
│   │   │
│   │   ├── context/ThemeContext.tsx          # Dark/light theme provider
│   │   ├── lib/utils.ts                     # Helper functions
│   │   ├── styles/design-tokens.css         # CSS custom properties
│   │   ├── index.css                        # Global styles
│   │   └── theme-transitions.css            # Theme switch animations
│   │
│   ├── electron/                            # ── Electron Desktop Shell ──
│   │   ├── main.js                          # Main process: window management, IPC
│   │   └── preload.js                       # Preload: secure context bridge
│   │
│   ├── public/                              # Static assets (logos, Monaco Editor)
│   ├── build/                               # Electron build resources (icons)
│   ├── index.html                           # HTML entrypoint
│   ├── package.json                         # Dependencies (44 production + 12 dev packages)
│   ├── vite.config.ts                       # Vite build configuration
│   ├── tailwind.config.js                   # Tailwind CSS customization
│   ├── postcss.config.js                    # PostCSS configuration
│   ├── tsconfig.json                        # TypeScript configuration
│   └── build_win.ps1                        # Windows Electron build script
│
├── 🛡️  admin-frontend/                       ══ Enterprise Command Center ══
│   │
│   ├── src/
│   │   ├── App.tsx                          # Admin app root with routing
│   │   ├── main.tsx                         # React DOM render entrypoint
│   │   │
│   │   ├── components/
│   │   │   ├── Layout.tsx                   # Admin layout shell with sidebar
│   │   │   ├── CommandPalette.tsx            # Admin ⌘K command palette
│   │   │   └── ui/                          # Admin UI primitives (button, card, input, label)
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx                # Main admin dashboard
│   │   │   ├── Login.tsx                    # Admin authentication
│   │   │   └── command-center/              # ── 25 Specialized Admin Modules ──
│   │   │       ├── Analytics.tsx            │ AutoHealing.tsx
│   │   │       ├── ChaosMonkey.tsx          │ ClusterFederation.tsx
│   │   │       ├── DatabaseControl.tsx      │ DefconControls.tsx
│   │   │       ├── DeveloperKeys.tsx        │ GlobalBroadcast.tsx
│   │   │       ├── HardwareGPU.tsx          │ KnowledgeGraph.tsx
│   │   │       ├── ModelHub.tsx             │ NetworkSecurity.tsx
│   │   │       ├── PlatformBranding.tsx     │ PlatformOutage.tsx
│   │   │       ├── PredictiveScaling.tsx    │ PromptFirewall.tsx
│   │   │       ├── RBACStudio.tsx           │ ReleaseManagement.tsx
│   │   │       ├── SubscriptionPlans.tsx    │ Telemetry.tsx
│   │   │       ├── TenantManager.tsx        │ TopologyMap.tsx
│   │   │       ├── UsageMonitoring.tsx      │ UserPlanManager.tsx
│   │   │       └── WorkflowOrchestrator.tsx
│   │   │
│   │   ├── hooks/useAuth.tsx, useHasPermission.ts
│   │   ├── lib/utils.ts
│   │   ├── index.css
│   │   └── theme-transitions.css
│   │
│   ├── package.json                         # Dependencies (29 production + 6 dev packages)
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── 🔊  TTS and STT/                          ══ Voice AI Agent (Standalone) ══
│   │
│   ├── main.py                              # CLI / API mode launcher
│   ├── voice_config.json                    # Voice persona configuration
│   ├── pyproject.toml                       # Python project metadata
│   ├── app/
│   │   ├── __init__.py
│   │   ├── agent.py                         # Voice AI agent orchestrator
│   │   ├── response_engine.py               # LLM response generation
│   │   ├── tts_engine.py                    # Text-to-Speech synthesis
│   │   ├── stt_engine.py                    # Speech-to-Text recognition
│   │   ├── tts_formatter.py                 # Indian number/abbreviation normalization
│   │   ├── http_api.py                      # FastAPI HTTP server
│   │   ├── cli.py                           # Interactive CLI interface
│   │   ├── config.py                        # Voice module configuration
│   │   └── models.py                        # Voice data models
│   └── tests/
│       ├── test_agent.py
│       ├── test_response_engine.py
│       └── test_tts_formatter.py
│
├── 🔄  .github/workflows/
│   └── ci.yml                               # CI pipeline: backend tests + frontend/admin builds
│
├── docker-compose.yml                       # Docker orchestration for services
├── package.json                             # Monorepo root — concurrently orchestrator
├── package-lock.json                        # Dependency lock file
├── .gitignore                               # Source protection configuration
└── README.md                                # This file
```

</details>

---

## 📡 API Reference

The full interactive **Swagger UI** is available at **`http://localhost:8080/docs`** when the backend is running.

### Endpoint Groups

| Group | Base Path | Routes | Description |
|:---|:---|:---:|:---|
| **Authentication** | `/api/auth/` | 13 | Register, login, logout, OTP, password reset, refresh |
| **OAuth** | `/api/oauth/` | 2 | Google OAuth 2.0 authorization & callback |
| **Chat** | `/api/chat/` | 15 | LLM streaming, history, shared links |
| **Voice** | `/api/voice/` | 2 | TTS synthesis, STT transcription |
| **RAG** | `/api/rag/` | 4 | Document upload, knowledge base, query, delete |
| **Code Agent** | `/api/code/` | 4 | Sandboxed Python execution |
| **Research** | `/api/research/` | 1 | Deep research with web + academic search |
| **Thinking** | `/api/thinking/` | 1 | Extended chain-of-thought reasoning |
| **Image** | `/api/image/` | 1 | AI image generation |
| **Snippets** | `/api/snippets/` | 3 | Code snippet CRUD |
| **Settings** | `/api/settings/` | 2 | User preferences and profile |
| **Admin** | `/api/admin/` | 35+ | User management, governance, security |
| **Subscriptions** | `/api/subscriptions/` | 10 | Plan management and billing |
| **Organizations** | `/api/organizations/` | 3 | Multi-tenant org management |
| **System** | `/api/system/` | 7 | Health checks, diagnostics, system info |
| **Metrics** | `/api/metrics` | 1 | Prometheus metrics export |
| **WebSocket** | `/ws/` | 9 | Agent, broadcast, and code execution streams |

### Key Endpoints

```http
# ── Authentication ──────────────────────────────────────────────
POST   /api/auth/register              # Create new account
POST   /api/auth/login                 # Authenticate → JWT token
POST   /api/auth/verify-otp            # Verify 2FA OTP code
POST   /api/auth/refresh               # Refresh expired JWT
POST   /api/auth/forgot-password       # Initiate password reset
POST   /api/auth/logout                # Invalidate session

# ── Streaming Chat ──────────────────────────────────────────────
POST   /api/chat/stream                # SSE streaming chat (primary LLM)
GET    /api/chat/history               # Get conversation history
POST   /api/chat/share                 # Generate shareable link
DELETE /api/chat/session/{id}          # Delete conversation

# ── Voice ───────────────────────────────────────────────────────
POST   /api/voice/tts                  # Text-to-Speech synthesis
POST   /api/voice/stt                  # Speech-to-Text transcription

# ── RAG Knowledge Base ──────────────────────────────────────────
POST   /api/rag/upload                 # Upload document to knowledge base
POST   /api/rag/query                  # Query knowledge base with AI
GET    /api/rag/documents              # List uploaded documents
DELETE /api/rag/documents/{id}         # Remove document

# ── Cognitive Engines ───────────────────────────────────────────
POST   /api/research/stream            # Deep research (web + academic)
POST   /api/thinking/stream            # Extended chain-of-thought

# ── Code Execution ──────────────────────────────────────────────
POST   /api/code/execute               # Run Python in local sandbox
WS     /ws/code                        # Live code execution streaming

# ── Image Generation ────────────────────────────────────────────
POST   /api/image/generate             # AI image generation

# ── Admin & System ──────────────────────────────────────────────
GET    /api/system/health              # System health check
GET    /api/metrics                    # Prometheus metrics export
```

---

## 🔐 Defense-in-Depth Security Model

InfiChat implements a **6-layer defense-in-depth** security architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 6: PRIVACY                              │
│  Local inference • No telemetry • Self-hosted • Zero data leak   │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 5: SANDBOX SECURITY                     │
│  AST Zero-Trust validation • Local subprocess execution           │
│  Ephemeral containers • No host filesystem access                │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 4: DATA SECURITY                        │
│  Field-level encryption • ORM-only queries • PII scrubbing       │
│  Sensitive log masking • Tamper-proof audit logging               │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 3: REQUEST PIPELINE                     │
│  Rate limiting • CORS • CSRF protection • Input sanitization     │
│  AI firewall • Usage tracking • Tenant isolation                 │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 2: AUTHORIZATION                        │
│  RBAC (user/admin/super-admin) • Permission guards               │
│  Admin-only endpoints • Two-person authorization                 │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 1: AUTHENTICATION                       │
│  Bcrypt (cost 12) • JWT (access + refresh) • OTP 2FA             │
│  Google OAuth 2.0 • Server-side token validation                 │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Controls | Key Files |
|:---|:---|:---|
| **1. Authentication** | Bcrypt (cost 12), JWT (60min access + 30d refresh), OTP 2FA, Google OAuth 2.0 | `security.py`, `auth.py`, `oauth.py` |
| **2. Authorization** | RBAC (3 roles), permission guards, admin isolation | `rbac.py`, `deps.py` |
| **3. Request Pipeline** | Rate limiting, CORS, CSRF, input sanitization, AI firewall, usage tracking, tenant isolation | `middleware/*.py` |
| **4. Data Security** | Field-level encryption, ORM-only queries, PII scrubbing, audit logging | `encryption.py`, `privacy_service.py`, `audit_logging.py` |
| **5. Sandbox** | Local subprocess isolation, Timeout enforcements, AST code safety validator | `sandbox_service.py` |
| **6. Privacy** | Local inference (Whisper, embeddings), zero telemetry, self-hosted | Architecture-level |

---

## 🚀 Deployment Guide

### Production Bare-Metal (PM2)
For production environments, use PM2 to manage the FastAPI and Vite servers.
```bash
npm install -g pm2
pm2 start "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8080" --name "infichat-backend"
pm2 start "cd frontend && npm run preview" --name "infichat-frontend"
pm2 start "cd admin-frontend && npm run preview" --name "infichat-admin"
pm2 save
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
    }

    # API + SSE (streaming support)
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;          # Required for SSE streaming
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # Admin Dashboard
    location /admin/ {
        proxy_pass http://localhost:5174;
    }
}
```

### Production Hardening Checklist

- [ ] Set `ENVIRONMENT=production` to disable debug mode and Swagger UI
- [ ] Rotate `SECRET_KEY` with a cryptographically random 256-bit value
- [ ] Enable HTTPS via Let's Encrypt (Certbot) for all public deployments
- [ ] Configure PostgreSQL connection pooling (`pgbouncer` recommended)
- [ ] Set `CORS_ORIGINS` to your production domain only
- [ ] Enable `ENABLE_PII_SCRUBBING=true` for compliance
- [ ] Configure Redis authentication with a strong password
- [ ] Set up automated backups for PostgreSQL and ChromaDB data volumes
- [ ] Monitor with Prometheus metrics (`/api/metrics`) + Grafana dashboards

---

## 📊 Performance Benchmarks

| Metric | Value | Conditions |
|:---|:---|:---|
| **Chat streaming latency** | < 200ms TTFB | Groq Llama 3.3 70B |
| **Token throughput** | ~300 tokens/sec | Groq provider |
| **TTS audio latency** | < 1 second | Edge-TTS neural synthesis |
| **STT transcription** | Real-time | Faster Whisper (base model, CPU) |
| **RAG retrieval** | < 100ms | FAISS with 10K documents |
| **API response (health)** | < 10ms | `/api/system/health` |
| **Frontend build** | < 30 seconds | Vite production build |
| **Backend startup** | < 5 seconds | With model preloading |
| **Concurrent users** | 100+ | Uvicorn with async handlers |

---

## 🗺️ Roadmap

### In Progress 🔨

- [ ] Mobile-responsive UI improvements
- [ ] Additional LLM provider integrations (Anthropic, Mistral, Cohere)
- [ ] WebRTC real-time voice chat

### Planned 📋

- [ ] i18n / internationalization support
- [ ] Automated test suite expansion (pytest + Playwright)
- [ ] Helm chart for Kubernetes deployment
- [ ] Additional Indic language TTS voices (Tamil, Kannada, Bengali)
- [ ] Plugin system for custom extensions
- [ ] Multi-modal file understanding (images, audio, video)
- [ ] Collaborative real-time editing
- [ ] Custom fine-tuned model integration

---

## 🐛 Troubleshooting Guide

<details>
<summary><strong>Backend won't start — ModuleNotFoundError</strong></summary>

```bash
# Ensure virtual environment is activated
cd backend && .\venv\Scripts\activate
pip install -r requirements.txt
```

</details>

<details>
<summary><strong>Database connection error</strong></summary>

```bash
# For PostgreSQL:
psql -U ai -d autoagent -h localhost
python fix_db_schema.py

# For SQLite (local dev):
# Database is auto-created at data/infichat.db
```

</details>



<details>
<summary><strong>TTS produces no audio</strong></summary>

```bash
# Test edge-tts directly
python -m edge_tts --voice en-IN-PrabhatNeural --text "Hello" --write-media test.mp3
```

</details>

<details>
<summary><strong>Whisper STT is slow</strong></summary>

```bash
# Use a smaller model for faster CPU inference
# In config.py: whisper_model = "tiny" or "base"
```

</details>

<details>
<summary><strong>ChromaDB vector dimension mismatch</strong></summary>

```bash
# Delete the ChromaDB collection and re-upload documents
rm -rf data/chromadb/
```

</details>

<details>
<summary><strong>Redis connection refused</strong></summary>

```bash
# If using bundled Redis (Windows):
cd redis && redis-server.exe redis.windows.conf

```

</details>

### Log Locations

| Log Location | Contents |
|:---|:---|
| `backend/backend_errors.log` | Backend Python errors |
| Browser DevTools → Network | Frontend API call errors |
| Terminal (uvicorn) | Real-time backend stdout |

---

## 🤝 Contributing

We welcome contributions from the community! Here's how to get involved:

### Getting Started

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/AI-Chatbot-InfiChat.git
cd AI-Chatbot-InfiChat

# 3. Create a feature branch
git checkout -b feature/your-amazing-feature

# 4. Make your changes following our code style

# 5. Test thoroughly

# 6. Commit with a descriptive message (conventional commits)
git commit -m "feat: add support for Whisper large-v3 model"

# 7. Push and open a Pull Request
git push origin feature/your-amazing-feature
```

### Contribution Guidelines

| Rule | Details |
|:---|:---|
| **Python Style** | Follow PEP 8 with docstrings on all functions |
| **Frontend** | TypeScript only — no plain JavaScript |
| **Commit Messages** | Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`) |
| **Documentation** | Update docs for any new features |
| **Security** | Never commit API keys or secrets |
| **Testing** | Add tests for new functionality |

### Areas We'd Love Help With

- [ ] Mobile-responsive UI improvements
- [ ] Additional LLM provider integrations (Anthropic, Mistral, Cohere)
- [ ] i18n / internationalization support
- [ ] Automated test suite expansion (pytest + Playwright)
- [ ] Helm chart for Kubernetes deployment
- [ ] Additional Indic language TTS voices
- [ ] WebRTC real-time voice chat
- [ ] Plugin system for custom extensions

---

## 📜 License

This project is licensed under the **MIT License** — you are free to use, modify, and distribute it for any purpose.

```
MIT License

Copyright (c) 2025-2026 Gugulothu Bhavith

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See the [LICENSE](LICENSE) file for full details.

---

## 🙏 Acknowledgements

InfiChat is built on the shoulders of incredible open-source projects:

| Project | Contribution |
|:---|:---|
| [**FastAPI**](https://fastapi.tiangolo.com/) | High-performance async Python web framework |
| [**React**](https://react.dev/) | Declarative UI library by Meta |
| [**ChromaDB**](https://www.trychroma.com/) | AI-native open-source embedding database |
| [**FAISS**](https://github.com/facebookresearch/faiss) | Efficient similarity search by Meta |
| [**Faster Whisper**](https://github.com/SYSTRAN/faster-whisper) | CTranslate2-powered speech recognition |
| [**Edge TTS**](https://github.com/rany2/edge-tts) | Microsoft Edge's neural TTS engine |
| [**Ollama**](https://ollama.com/) | Local LLM runner made simple |
| [**sentence-transformers**](https://www.sbert.net/) | State-of-the-art sentence embeddings |
| [**Electron**](https://www.electronjs.org/) | Cross-platform desktop applications |
| [**Three.js**](https://threejs.org/) | JavaScript 3D library |
| [**Recharts**](https://recharts.org/) | Composable charting library for React |
| [**Radix UI**](https://www.radix-ui.com/) | Accessible component primitives |
| [**Tailwind CSS**](https://tailwindcss.com/) | Utility-first CSS framework |
| [**Vite**](https://vitejs.dev/) | Lightning-fast frontend tooling |

---

## 📞 Contact

| Channel | Link |
|:---|:---|
| **LinkedIn** | [linkedin.com/in/gugulothubhavith](https://www.linkedin.com/in/gugulothubhavith) |
| **GitHub** | [github.com/gugulothubhavith](https://github.com/gugulothubhavith) |
| **Issues** | [Report a Bug](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat/issues) |
| **Features** | [Request a Feature](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat/issues) |
| **Discussions** | [Join Discussions](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat/discussions) |

---

<div align="center">

**Built with ❤️ for the Open Source AI Community**

*Empowering individuals and organizations to own their AI — privately, securely, and completely.*

<br/>

<strong>Designed & Developed by Gugulothu Bhavith</strong>

*Empowering Autonomy Through Sovereign AI*

<br/>

[![Star on GitHub](https://img.shields.io/github/stars/gugulothubhavith/AI-Chatbot-InfiChat?style=social)](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat)
[![Fork on GitHub](https://img.shields.io/github/forks/gugulothubhavith/AI-Chatbot-InfiChat?style=social)](https://github.com/gugulothubhavith/AI-Chatbot-InfiChat/fork)

</div>
