<div align="center">

<br/>

<pre>
██ ███    ██ ███████ ██  ██████  ██   ██  █████  ████████
██ ████   ██ ██      ██ ██       ██   ██ ██   ██    ██   
██ ██ ██  ██ █████   ██ ██       ███████ ███████    ██   
██ ██  ██ ██ ██      ██ ██       ██   ██ ██   ██    ██   
██ ██   ████ ██      ██  ██████  ██   ██ ██   ██    ██   
</pre>

<h3>InfiChat — AI Chat Platform</h3>

<p><em>Multi-Model &nbsp;·&nbsp; Agentic Squads &nbsp;·&nbsp; Deep Research &nbsp;·&nbsp; RAG &nbsp;·&nbsp; Voice &nbsp;·&nbsp; Real-time Groups &nbsp;·&nbsp; Full Admin Console</em></p>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![TanStack](https://img.shields.io/badge/TanStack_Router-1.x-FF4154?style=for-the-badge&logo=react-query&logoColor=white)](https://tanstack.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-FF6B35?style=for-the-badge&logo=databricks&logoColor=white)](https://trychroma.com)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-Nemotron_550B-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Stars](https://img.shields.io/github/stars/gugulothubhavith/Chatbot-InfiChat?style=for-the-badge&logo=github&logoColor=white&color=gold)](https://github.com/gugulothubhavith/Chatbot-InfiChat/stargazers)

<br/>

> **InfiChat** is a production-grade, enterprise-ready Generative AI Chat Platform.  
> Every model call, every user message, every document — **stays on your infrastructure. Forever.**

<br/>

**[🚀 Quick Start](#-quick-start)** · **[📸 Feature Showcase](FEATURES.md)** · **[✨ Features](#-features)** · **[🏗 Architecture](#-architecture)** · **[🤖 AI Models](#-ai-model-ecosystem)** · **[🔌 Connectors](#-integrations--connectors)** · **[🛡 Security](#-security--compliance)** · **[📜 License](#-license)**

---

</div>

<br/>

## 📑 Table of Contents

- [✨ Features](#-features)
- [🏗 Architecture](#-architecture)
- [🤖 AI Model Ecosystem](#-ai-model-ecosystem)
- [🔌 Integrations & Connectors](#-integrations--connectors)
- [🚀 Quick Start](#-quick-start)
- [📁 Project Structure](#-project-structure)
- [⚙️ Configuration Reference](#-configuration-reference)
- [🐳 Docker Services](#-docker-services)
- [🗃️ Database & Migrations](#-database--migrations)
- [🔊 Voice (STT & TTS)](#-voice-stt--tts)
- [🎨 Image Generation](#-image-generation)
- [🧠 Agentic Pipelines](#-agentic-pipelines)
- [👥 Real-time Collaboration](#-real-time-collaboration)
- [💳 Billing & Subscriptions](#-billing--subscriptions)
- [🛡 Security & Compliance](#-security--compliance)
- [🖥️ Admin Console](#-admin-console)
- [📡 API Reference](#-api-reference)
- [📊 Observability](#-observability)
- [🌐 Production Deployment](#-production-deployment)
- [🧪 Testing](#-testing)
- [🗺️ Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [🙏 Acknowledgements](#-acknowledgements)

<br/>

---

## ✨ Features

InfiChat is not a chatbot. It is a **complete AI operating system** — every feature you'd expect from a frontier AI product, built entirely on your own infrastructure.

> 📸 **[Click here to view the detailed visual Feature Showcase with screenshots (FEATURES.md)](FEATURES.md)**

<br/>

<table>
<tr>
<td width="50%" valign="top">

### 🧠 AI Core Engine
- **Multi-model routing** with automatic failover — NVIDIA NIM, Groq, Google Gemini, OpenRouter, all in one
- **Key Pool** — round-robin multi-key rotation with per-provider rate-limit tracking; no single key is ever a SPOF
- **Deep Research** — fully autonomous, multi-step web research agent with structured citations, sub-query decomposition, and synthesis
- **Deep Thinking** — extended chain-of-thought reasoning pipeline, separate from standard completions
- **Web Search Agent** — real-time SearxNG-powered search fused with LLM synthesis; privacy-first, no Google/Bing dependency
- **Multi-Agent Squad** — Planner → Researcher → Coder → Reviewer autonomous pipeline with live progress streaming
- **Persistent Memory** — background memory extraction per user; automatically recalled on relevant future conversations
- **Vision / Multi-modal** — native image understanding, inline image attachment analysis (Gemini Flash)
- **Code Agent** — isolated Docker sandbox execution per session; supports Python, Node.js, Bash, R, and more
- **AI Firewall** — pre-generation prompt screening with customizable rules
- **Safety Scanner** — post-generation output validation layer
- **Context Window Management** — automatic sliding-window truncation + tiktoken-accurate token counting

</td>
<td width="50%" valign="top">

### 🗄️ Knowledge & RAG
- **Dual-mode vector store** — ChromaDB (production, Docker-native) with FAISS fallback for zero-dependency local dev
- **Per-chat RAG** — attach any file directly to any conversation; live retrieval without polluting other sessions
- **Project Knowledge Base** — persistent, isolated per-project vector collection with independent embedding spaces
- **Project Insights** — AI-generated summaries of everything in a knowledge base
- **Reranking pipeline** — Voyage AI `rerank-2.5` for precision-first document ordering
- **Multi-format ingestion** — PDF (pypdf + pdfplumber), DOCX, TXT, Markdown, source code
- **GPU-accelerated parsing** — Unstructured API for OCR, table extraction, and image-within-PDF handling
- **Web scraping** — Playwright + Trafilatura pipeline for live URL ingestion into any knowledge base
- **arxiv integration** — academic paper search and retrieval built into the research pipeline
- **Semantic chunking** — intelligent document splitting that respects paragraph and section boundaries
- **Embedding models** — BGE small/large (local, free) + Voyage AI voyage-3 (API, premium precision)

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 👥 Collaboration
- **Real-time group chats** — multi-user WebSocket rooms with Redis pub/sub fan-out; AI participates inline
- **Group moderation** — admin controls, member management, message deletion, group archiving
- **Shared Projects** — invite-link sharing with per-member role assignment (Viewer / Editor / Admin)
- **Project Templates** — one-click pre-built AI workflows (Research, Code Review, Q&A, etc.)
- **Family Plan** — sub-account delegation with a parent account controlling permissions
- **Team/Org Plan** — seat-based management with billing rollup to the organization owner
- **Code Sessions** — collaborative live coding environments with shared sandbox state
- **Shared Links** — generate shareable read-only links to any conversation
- **Push Notifications** — VAPID web-push to all registered devices across platforms
- **In-app Notification Centre** — grouped, real-time notifications with read/unread state

</td>
<td width="50%" valign="top">

### 🎨 Media & Voice
- **Text-to-Image** — FLUX.1-Schnell via NVIDIA API, inline in the chat stream
- **Image Gallery** — full-resolution image history with soft-delete, bulk actions, and configurable retention/purge
- **Image in Projects** — images generated inside a project are scoped to and searchable within it
- **Voice STT** — Whisper large-v3 / turbo via Groq (cloud) or faster-whisper (local, fully offline)
- **Voice TTS** — Unreal Speech Sierra (natural, human-like) + Edge-TTS (free, no key)
- **Indic language support** — regional language TTS via Edge-TTS voice selection
- **Real-time voice transcription** — stream audio chunks and get progressive text back
- **Attachment pipeline** — multi-format file extractor: PDF, DOCX, PPTX, images, source code, plain text
- **Invoice PDF generation** — client-side PDF invoices using jsPDF, auto-stamped with platform branding

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🔐 Security & Compliance
- **JWT auth** — HS256 signed tokens, configurable expiry, refresh rotation
- **bcrypt hashing** — configurable cost factor; resistant to GPU brute-force
- **TOTP MFA** — RFC 6238-compliant two-factor authentication (Google Authenticator, Authy)
- **Google OAuth 2.0** — social sign-in with offline access token handling
- **GitHub OAuth** — developer-friendly alternative sign-in
- **Refresh token revocation** — immediate logout across all sessions
- **TrustedHostMiddleware** — blocks Host header spoofing attacks
- **CORS allowlist** — no wildcard origins in production; strict domain enforcement
- **Rate limiting** — SlowAPI + Redis sliding-window per endpoint per user
- **GeoIP routing** — jurisdiction-aware model and pricing selection
- **GDPR consent service** — affirmative consent recording, withdrawal support, audit trail
- **Data retention policies** — configurable automatic soft → hard delete pipeline
- **Cookie banner** — granular consent preferences with persistent storage
- **AI content moderation** — configurable keyword block lists + LLM-based classification

</td>
<td width="50%" valign="top">

### 🖥️ Admin Console
- **Real-time KPI Dashboard** — active users, DAU/MAU, token usage, revenue, error rates
- **User Management** — search, filter, impersonate, suspend, ban, role assignment, account erasure
- **Analytics** — per-model usage breakdown, per-endpoint latency, hourly/daily/monthly views
- **Model Manager** — hot-swap AI models without restarting any service
- **API Key Manager** — per-provider key pool management from the UI
- **Subscription Engine** — view/manage all active plans, override billing, grant/revoke trials
- **Coupon Engine** — create and manage percentage and fixed-amount discount codes
- **Platform Profile** — legal entity name, invoice branding, support contacts, social links
- **Feature Flags** — per-feature kill switches (disable image gen, voice, RAG, etc. instantly)
- **Incident Manager** — status page editor with severity levels and incident timeline
- **Database Explorer** — live schema inspector, table browser, query runner (read-only safe mode)
- **Safety & Firewall** — manage blocked patterns, review flagged content, configure AI safety thresholds
- **Broadcast** — platform-wide or targeted user announcements (banner, email, push)
- **Staff Management** — internal team accounts with elevated permissions separate from user RBAC
- **Audit Logs** — immutable action log: every admin action timestamped, attributed, and stored
- **Supervision / Parental Controls** — per-account usage limits, timezone-aware quiet hours, feature restrictions
- **System Health** — live Docker service status, memory/CPU, queue depth, cache hit ratio
- **Releases / Changelog** — in-app release notes editor for user-facing changelog

</td>
</tr>
</table>

<br/>

---

## 🏗 Architecture

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           InfiChat Platform                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ┌─────────────────┐   ┌─────────────────┐   ┌───────────────────────────┐  ║
║   │  Frontend-New   │   │  Admin Console  │   │     Mobile / PWA          │  ║
║   │  React 19       │   │  React + Vite   │   │  (Progressive Web App)    │  ║
║   │  TanStack Start │   │  TypeScript     │   │  Push Notifications       │  ║
║   │  Tailwind v4    │   │  shadcn/ui      │   │  Offline-capable          │  ║
║   │  Framer Motion  │   │                 │   │                           │  ║
║   └────────┬────────┘   └────────┬────────┘   └─────────────┬─────────────┘  ║
║            │ :5173               │ :5174                     │                ║
║            └────────────────────┬┴───────────────────────────┘                ║
║                                 │           (nginx reverse proxy)              ║
║                                 ▼  :8000                                       ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │                         FastAPI Backend (ASGI)                          │ ║
║   │                                                                         │ ║
║   │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │ ║
║   │  │  REST API  │  │  WebSocket  │  │     SSE      │  │  Background   │  │ ║
║   │  │  /api/v1   │  │   /ws/*     │  │   Streams    │  │   Tasks       │  │ ║
║   │  │  47 routes │  │  4 channels │  │  (chat/img)  │  │  (memory/idx) │  │ ║
║   │  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │ ║
║   │        └────────────────┴─────────────────┴──────────────────┘          │ ║
║   │                                    │                                     │ ║
║   │          ┌─────────────────────────┼──────────────────────┐             │ ║
║   │          ▼                         ▼                       ▼             │ ║
║   │  ┌──────────────┐       ┌─────────────────┐    ┌──────────────────────┐ │ ║
║   │  │  LLM Router  │       │   RAG Service   │    │   Agent Orchestrator │ │ ║
║   │  │  Key Pool    │       │   ChromaDB      │    │   Deep Research      │ │ ║
║   │  │  AI Firewall │       │   FAISS         │    │   Web Search         │ │ ║
║   │  │  AI Safety   │       │   Embeddings    │    │   Code Sandbox       │ │ ║
║   │  │  Failover    │       │   Reranker      │    │   Multi-Agent Squad  │ │ ║
║   │  └──────┬───────┘       └─────────────────┘    └──────────────────────┘ │ ║
║   └─────────┼───────────────────────────────────────────────────────────────┘ ║
║             │                                                                  ║
║   ┌─────────▼──────┐  ┌─────────────┐  ┌──────────┐  ┌─────────────────────┐ ║
║   │  AI Providers  │  │ PostgreSQL  │  │  Redis   │  │     ChromaDB        │ ║
║   │                │  │ (primary DB)│  │ (cache   │  │  (vector database)  │ ║
║   │  NVIDIA NIM    │  │ 38 ORM      │  │  pub/sub │  │  per-project        │ ║
║   │  Groq          │  │  models     │  │  rate    │  │  collections        │ ║
║   │  Google Gemini │  │ Alembic     │  │  limit)  │  │  BGE / Voyage       │ ║
║   │  OpenRouter    │  │  migrations │  │          │  │  embeddings         │ ║
║   └────────────────┘  └─────────────┘  └──────────┘  └─────────────────────┘ ║
║                                                                               ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ ║
║   │    SearxNG       │  │  Unstructured    │  │     Docker Sandbox         │ ║
║   │  (self-hosted    │  │  API             │  │   (code execution)         │ ║
║   │   web search)    │  │  (GPU doc parse) │  │   throwaway containers     │ ║
║   │  :8080           │  │  :8002           │  │   per session              │ ║
║   └──────────────────┘  └──────────────────┘  └────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Complete Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend Framework** | React + TanStack Router + TanStack Start | React 19, Router 1.x | UI + SSR-ready routing |
| **Styling** | Tailwind CSS v4 + shadcn/ui + Radix UI | Tailwind 4.x | Design system |
| **Animation** | Framer Motion | 12.x | Page transitions, micro-animations |
| **State Management** | Zustand + TanStack Query | Latest | Local + server state |
| **Code Editor** | Monaco Editor | Latest | In-browser code editing |
| **PDF Generation** | jsPDF | Latest | Invoice PDF generation |
| **Backend Framework** | FastAPI + Uvicorn | 0.109 / 0.27 | ASGI API server |
| **ORM** | SQLAlchemy 2 + Alembic | 2.0 / 1.13 | Database models + migrations |
| **Primary Database** | PostgreSQL 15 | 15 | Transactional data store |
| **Cache / PubSub** | Redis 7 | 7-alpine | Sessions, pub/sub, rate limiting |
| **Vector Database** | ChromaDB | 0.5 (pinned) | Semantic search collections |
| **Vector Fallback** | FAISS | ≥1.7.4 | Zero-dependency local dev |
| **Embeddings (local)** | sentence-transformers (BGE) | Latest | Free, offline embeddings |
| **Embeddings (premium)** | Voyage AI voyage-3 | API | High-precision embeddings |
| **Reranking** | Voyage AI rerank-2.5 | API | Precision-first retrieval |
| **Tokenizer** | tiktoken | ≥0.6 | Accurate token counting |
| **Auth** | python-jose + bcrypt + pyotp | Pinned | JWT + password + MFA |
| **OAuth** | Google OAuth 2.0 + GitHub OAuth | — | Social sign-in |
| **Payments** | Stripe | ≥8.0 | Subscriptions, invoices, webhooks |
| **Document Parsing** | Unstructured API + pypdf + pdfplumber + python-docx | — | Multi-format ingestion |
| **Web Scraping** | Playwright + Trafilatura + BeautifulSoup4 | — | URL → knowledge base |
| **Voice STT** | faster-whisper (local) + Groq Whisper API | — | Speech-to-text |
| **Voice TTS** | Unreal Speech + Edge-TTS | — | Text-to-speech |
| **Rate Limiting** | SlowAPI | Latest | Redis-backed per-endpoint limits |
| **Containerization** | Docker + Docker Compose | 24+ | Full stack orchestration |

<br/>

---

## 🤖 AI Model Ecosystem

InfiChat routes every request through a **multi-provider key pool** with automatic failover. If one key hits a rate limit, the next key in the pool takes over — transparently, with no error shown to the user.

| Feature | Model | Provider | Notes |
|---------|-------|----------|-------|
| **Default Chat** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | Flagship reasoning model |
| **Fast Chat** | `llama-3.1-70b-versatile` | Groq | Ultra-low latency |
| **Deep Research** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | Extended context + citations |
| **Research Fast Loop** | `openai/gpt-oss-120b` | OpenRouter | Sub-query generation |
| **Web Search Synthesis** | `nvidia/llama-3_3-nemotron-super-49b-v1_5` | NVIDIA NIM | Search result fusion |
| **Vision / Image Understanding** | `gemini-1.5-flash` / `gemini-3-flash-preview` | Google Gemini | Inline image analysis |
| **Multi-Agent Planner** | `z-ai/glm-5.2` | NVIDIA NIM | Task decomposition |
| **Multi-Agent Coder** | `z-ai/glm-5.2` | NVIDIA NIM | Code generation in loop |
| **Multi-Agent Reviewer** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | Code review + critique |
| **Memory Extraction** | `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA NIM | Background memory distillation |
| **RAG Synthesis** | Configurable | Any provider | Per-project override |
| **Embeddings (default)** | `BAAI/bge-small-en-v1.5` | Local / HuggingFace | Free, no API key |
| **Embeddings (large)** | `BAAI/bge-large-en-v1.5` | Local / HuggingFace | Higher precision, free |
| **Embeddings (premium)** | `voyage-3` | Voyage AI | State-of-art precision |
| **Reranking** | `rerank-2.5` | Voyage AI | Post-retrieval precision |
| **STT (primary)** | `whisper-large-v3` | Groq | Cloud, fastest |
| **STT (turbo)** | `whisper-large-v3-turbo` | Groq | 8x faster, lower quality |
| **STT (offline)** | `faster-whisper` | Local | No internet required |
| **TTS (primary)** | Sierra | Unreal Speech | Human-like, emotive |
| **TTS (free)** | Any Edge-TTS voice | Microsoft Edge | No API key, 100+ voices |
| **Image Generation** | `black-forest-labs/flux-1-schnell` | NVIDIA API | FLUX.1-Schnell, fastest |

> See [`.env.models`](.env.models) for the complete model manifest with every configuration variable.

<br/>

---

## 🔌 Integrations & Connectors

InfiChat ships with a full **OAuth 2.0 connector framework**. Users authenticate once, and the AI can then read from and write to their connected services as a tool call — natively, inside any conversation.

| Category | Service | Read | Write | Notes |
|----------|---------|------|-------|-------|
| **Code** | GitHub | ✅ repos, issues, PRs, files, commits | ✅ comments, issues | OAuth App |
| **Code** | GitLab | ✅ projects, MRs, pipelines, files | ✅ comments, issues | OAuth App |
| **Google** | Google Drive | ✅ files, folders, search | ✅ upload, create | OAuth 2.0 |
| **Google** | Gmail | ✅ emails, threads, labels | ✅ send, reply, draft | OAuth 2.0 |
| **Google** | Google Calendar | ✅ events, calendars | ✅ create, update events | OAuth 2.0 |
| **Microsoft** | Outlook / Exchange | ✅ emails, folders | ✅ send, reply | OAuth 2.0 |
| **Microsoft** | OneDrive | ✅ files, folders | ✅ upload, create | OAuth 2.0 |
| **Microsoft** | Calendar | ✅ events, rooms | ✅ create, update | OAuth 2.0 |
| **Cloud Storage** | Dropbox | ✅ files, folders, search | ✅ upload, create | OAuth 2.0 |
| **Cloud Storage** | Box | ✅ files, folders | ✅ upload, create | OAuth 2.0 |
| **Notes** | Notion | ✅ pages, databases, blocks | ✅ create, update pages | OAuth 2.0 |
| **Tasks** | Todoist | ✅ tasks, projects, labels | ✅ create, update, complete | OAuth 2.0 |
| **Tasks** | Linear | ✅ issues, projects, cycles | ✅ create, update issues | OAuth 2.0 |
| **Tasks** | Asana | ✅ tasks, projects, workspaces | ✅ create, update tasks | OAuth 2.0 |
| **Tasks** | Jira | ✅ issues, boards, sprints | ✅ create, update issues | OAuth 2.0 |
| **Tasks** | ClickUp | ✅ tasks, spaces, lists | ✅ create, update tasks | OAuth 2.0 |
| **Tasks** | Trello | ✅ cards, boards, lists | ✅ create, update cards | OAuth 2.0 |
| **Messaging** | Slack | ✅ channels, messages, threads | ✅ send messages | OAuth 2.0 |
| **Messaging** | Discord | ✅ guilds, channels, messages | ✅ send messages | OAuth 2.0 |
| **CRM** | HubSpot | ✅ contacts, companies, deals | ✅ create, update records | OAuth 2.0 |
| **CRM** | Zendesk | ✅ tickets, users, orgs | ✅ create, update tickets | OAuth 2.0 |
| **Design** | Figma | ✅ files, frames, comments | ✅ add comments | OAuth 2.0 |
| **Data** | Airtable | ✅ bases, tables, records | ✅ create, update records | OAuth 2.0 |
| **Meetings** | Zoom | ✅ meetings, recordings | ✅ create meetings | OAuth 2.0 |
| **Meetings** | Calendly | ✅ event types, availability | — | OAuth 2.0 |
| **Music** | Spotify | ✅ playback, playlists, library | ✅ queue tracks | OAuth 2.0 |

> Each connector is **disabled by default**. Enable by adding `CLIENT_ID` + `CLIENT_SECRET` to `.env`.  
> See [`.env.example`](.env.example) for OAuth app registration links for every service.

<br/>

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum | Recommended | Notes |
|-------------|---------|-------------|-------|
| Docker Desktop | 24+ | Latest | Must have Compose v2 |
| RAM | 8 GB | 16 GB | 16 GB if using all services |
| Disk | 10 GB | 20 GB | For volumes & model cache |
| OS | Any | Windows / Linux | macOS supported too |
| API Key | 1 of: NVIDIA / Groq / Google | All three | At least one is required |

### Step 1 — Clone

```bash
git clone https://github.com/gugulothubhavith/Chatbot-InfiChat.git
cd Chatbot-InfiChat
```

### Step 2 — Configure

```bash
# Copy environment templates
cp .env.example .env
cp backend/.env.example backend/.env
cp admin-frontend/.env.example admin-frontend/.env
cp Frontend-New/.env.example Frontend-New/.env
```

Open `.env` and fill in at minimum:

```bash
# ── At least ONE AI provider ──────────────────────────────────────────────────
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxx     # https://build.nvidia.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx         # https://console.groq.com
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxx     # https://aistudio.google.com

# ── Security (generate these, never share) ────────────────────────────────────
SECRET_KEY=                   # openssl rand -hex 64
CONNECTOR_ENCRYPTION_KEY=     # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# ── Optional: Stripe for billing ──────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
```

### Step 3 — Launch

**Windows (one-click menu):**
```cmd
docker-manage.bat
```
→ Press **[1]** Start All Services

**All platforms:**
```bash
docker compose up -d
```

### Step 4 — Access

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Chat App** | http://localhost:5173 | Register a new account |
| **Admin Console** | http://localhost:5174 | Check logs for seeded admin password |
| **API Docs (Swagger)** | http://localhost:8000/docs | — |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | — |
| **Health Check** | http://localhost:8000/health | — |
| **Prometheus Metrics** | http://localhost:8000/metrics | — |

```bash
# Find the auto-generated admin password (first boot only)
docker compose logs backend | grep -i "admin\|seed\|password"
```

<br/>

---

## 📁 Project Structure

```
InfiChat/                                     ← Repository root
│
├── 📄 README.md                              ← This file
├── 📄 LICENSE                                ← Proprietary license
├── 📄 .gitignore                             ← 16-section deny-by-default rules
├── 📄 .env.example                           ← Root environment template
├── 📄 .env.models                            ← AI model manifest (no secrets)
├── 📄 docker-compose.yml                     ← 8-service orchestration
├── 📄 docker-manage.bat                      ← Windows one-click management
│
├── 🐍 backend/                               ← FastAPI application
│   ├── app/
│   │   ├── api/                              ← 47 route modules
│   │   │   ├── auth.py                       ← Auth, OAuth, MFA, sessions
│   │   │   ├── chat.py                       ← Chat SSE streaming
│   │   │   ├── image.py                      ← Image generation + gallery
│   │   │   ├── voice.py                      ← STT + TTS
│   │   │   ├── rag.py                        ← RAG upload + query
│   │   │   ├── research.py                   ← Deep Research SSE
│   │   │   ├── web_search.py                 ← Web Search SSE
│   │   │   ├── projects.py                   ← Project CRUD + knowledge base
│   │   │   ├── project_sharing.py            ← Invite links + permissions
│   │   │   ├── group_chat.py                 ← Group management
│   │   │   ├── group_messages.py             ← Group message REST
│   │   │   ├── ws_groups.py                  ← Group WebSocket fan-out
│   │   │   ├── ws_agent.py                   ← Multi-agent WebSocket stream
│   │   │   ├── connectors.py                 ← OAuth connector framework
│   │   │   ├── family.py                     ← Family plan management
│   │   │   ├── mfa.py                        ← TOTP MFA setup/verify
│   │   │   ├── notifications.py              ← Push + in-app notifications
│   │   │   ├── code_sessions.py              ← Code sandbox sessions
│   │   │   ├── subscriptions.py              ← Stripe billing
│   │   │   ├── platform_profile.py           ← Platform identity config
│   │   │   ├── reports.py                    ← User reports + moderation
│   │   │   ├── admin_analytics.py            ← Admin analytics API
│   │   │   ├── admin_audit_api.py            ← Immutable audit log
│   │   │   ├── admin_coupons.py              ← Coupon management
│   │   │   ├── admin_database.py             ← Live DB inspector
│   │   │   ├── admin_explorer.py             ← File/resource explorer
│   │   │   ├── admin_safety.py               ← AI safety controls
│   │   │   ├── admin_staff.py                ← Staff team management
│   │   │   ├── oauth_github.py               ← GitHub OAuth
│   │   │   └── api_keys.py                   ← Provider key pool management
│   │   │
│   │   ├── core/                             ← Cross-cutting concerns
│   │   │   ├── config.py                     ← Settings (pydantic-settings)
│   │   │   ├── security.py                   ← JWT, bcrypt, token helpers
│   │   │   ├── deps.py                       ← FastAPI dependency injectors
│   │   │   ├── net.py                        ← Trusted proxy / IP utilities
│   │   │   └── push.py                       ← VAPID web-push helpers
│   │   │
│   │   ├── models/                           ← 38 SQLAlchemy ORM models
│   │   ├── schemas/                          ← Pydantic v2 schemas
│   │   ├── services/                         ← 44 business logic modules
│   │   │   ├── chat_service.py               ← Core chat orchestration
│   │   │   ├── llm_router.py                 ← Multi-provider key pool
│   │   │   ├── rag_service.py                ← RAG pipeline
│   │   │   ├── group_realtime.py             ← Redis pub/sub fan-out
│   │   │   ├── group_service.py              ← Group business logic
│   │   │   ├── image_storage.py              ← Image generation + storage
│   │   │   ├── voice_service.py              ← TTS pipeline
│   │   │   ├── memory_service.py             ← Persistent memory extraction
│   │   │   ├── connector_service.py          ← OAuth token management
│   │   │   ├── connector_tools.py            ← AI tool call implementations
│   │   │   ├── coupon_service.py             ← Discount code logic
│   │   │   ├── subscription_service.py       ← Stripe + plan management
│   │   │   ├── consent_service.py            ← GDPR consent recording
│   │   │   ├── admin_audit.py                ← Audit log writer
│   │   │   ├── notification_service.py       ← Push + in-app dispatch
│   │   │   ├── project_service.py            ← Project CRUD
│   │   │   ├── project_knowledge.py          ← Per-project RAG
│   │   │   ├── project_search.py             ← Semantic search
│   │   │   ├── project_templates.py          ← Template seeding
│   │   │   ├── project_access.py             ← Permission enforcement
│   │   │   └── deep_research/ · web_search/  ← Agentic pipelines (private)
│   │   │
│   │   ├── middleware/
│   │   │   ├── usage_tracker.py              ← Per-request token metering
│   │   │   └── maintenance.py                ← Maintenance mode middleware
│   │   │
│   │   └── main.py                           ← App factory + startup
│   │
│   ├── alembic/                              ← DB migrations (git-tracked)
│   │   └── versions/                         ← 16+ migration files
│   ├── tests/                                ← Test suite
│   ├── scripts/                              ← One-off admin scripts
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
│
├── ⚛️  Frontend-New/                         ← Primary UI (React 19)
│   ├── src/
│   │   ├── routes/                           ← 25 file-based TanStack routes
│   │   ├── components/                       ← Shared UI components
│   │   ├── hooks/                            ← Custom React hooks
│   │   ├── stores/                           ← Zustand state stores
│   │   └── lib/                              ← Utility functions
│   ├── Dockerfile
│   └── package.json
│
├── 🖥️  admin-frontend/                       ← Admin console (React + Vite)
│   ├── src/
│   │   ├── pages/                            ← 30 admin page components
│   │   ├── components/                       ← Admin UI components
│   │   └── lib/                              ← Admin utilities + API client
│   ├── Dockerfile
│   └── package.json
│
└── 🔧 searxng-data/                          ← SearxNG search engine config
```

<br/>

---

## ⚙️ Configuration Reference

### Environment Files

| File | Purpose | Safe to Commit |
|------|---------|----------------|
| `.env.example` | Root compose template | ✅ Yes — has no real values |
| `.env` | Live root secrets | ❌ Never — gitignored |
| `backend/.env.example` | Backend template | ✅ Yes |
| `backend/.env` | Backend live secrets | ❌ Never — gitignored |
| `admin-frontend/.env.example` | Admin UI template | ✅ Yes |
| `Frontend-New/.env.example` | Frontend template | ✅ Yes |
| `.env.models` | AI model manifest | ✅ Yes — no credentials |

### Key Environment Variables

```bash
# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+psycopg2://user:pass@postgres:5432/infichat

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── Vector DB ─────────────────────────────────────────────────────────────────
RAG_BACKEND=chroma                  # 'chroma' | 'faiss'
CHROMA_URL=http://chromadb:8000     # Must use service name inside Docker

# ── External Services ─────────────────────────────────────────────────────────
SEARXNG_URL=http://searxng:8080
UNSTRUCTURED_URL=http://unstructured-api:8000

# ── Image Storage ─────────────────────────────────────────────────────────────
IMAGE_STORAGE_DIR=/data/images
IMAGE_GENERATION_TIMEOUT=90         # seconds
IMAGE_PURGE_AFTER_DAYS=30           # soft-delete → hard-delete window

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY=                         # 64+ random bytes (openssl rand -hex 64)
CONNECTOR_ENCRYPTION_KEY=           # Fernet key for OAuth token encryption

# ── Admin Seeding (first boot only) ──────────────────────────────────────────
SEED_ADMIN_EMAIL=admin@example.com
SEED_ADMIN_PASSWORD=                # Leave empty → auto-generated once

# ── Push Notifications ────────────────────────────────────────────────────────
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_SUBJECT=mailto:admin@yourdomain.com

# ── Trusted Proxy (Docker bridge CIDR ranges) ─────────────────────────────────
TRUSTED_PROXY_IPS=172.16.0.0/12,192.168.0.0/16,10.0.0.0/8,127.0.0.1

# ── GeoIP / Region ───────────────────────────────────────────────────────────
GEOIP_DB_PATH=/data/GeoLite2-City.mmdb

# ── SMTP / Email ──────────────────────────────────────────────────────────────
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=
SMTP_FROM_NAME=InfiChat
SMTP_FROM_EMAIL=noreply@example.com

# ── Stripe ────────────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
PUBLIC_BASE_URL=https://chat.yourdomain.com
```

<br/>

---

## 🐳 Docker Services

```
Service             Image                    Port    Role
──────────────────  ───────────────────────  ──────  ──────────────────────────────
postgres            postgres:15              5432    Primary relational database
redis               redis:7-alpine           6379    Cache, pub/sub, rate limiting
chromadb            chromadb/chroma:0.5.0    8001    Vector database (version pinned)
searxng             searxng/searxng          8080    Self-hosted privacy web search
backend             infichat/backend         8000    FastAPI ASGI API server
frontend-new        infichat/frontend-new    5173    React 19 primary UI
admin-frontend      infichat/admin           5174    Admin operator console
unstructured-api    downloads.unstructured…  8002    GPU doc parsing (OCR, tables)
```

> **ChromaDB version is pinned to 0.5.x.** Upgrading without migrating the vector store will corrupt all RAG collections.

### Health Checks

Every service has a defined health check. The backend waits for PostgreSQL, Redis, and ChromaDB to be fully ready before starting. The frontends wait for the backend.

```bash
# View live health of all services
docker compose ps

# Follow backend startup logs
docker compose logs -f backend

# Run DB migrations manually
docker compose exec backend alembic upgrade head

# Dependency CVE audit
docker compose exec backend pip-audit

# Open a psql shell
docker compose exec postgres psql -U infichat infichat
```

<br/>

---

## 🗃️ Database & Migrations

InfiChat uses **Alembic** for database migrations. Migrations apply automatically on backend startup.

```bash
# Create a migration after changing SQLAlchemy models
docker compose exec backend alembic revision --autogenerate -m "describe_change"

# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Rollback one step
docker compose exec backend alembic downgrade -1

# View migration history
docker compose exec backend alembic history --verbose

# View current DB revision
docker compose exec backend alembic current
```

Migration files live in `backend/alembic/versions/` and are the **single source of truth for the production schema**. They are tracked in git.

<br/>

---

## 🧠 Agentic Pipelines

### Deep Research

Fully autonomous multi-step research agent:

1. **Query decomposition** — breaks the user's question into parallel sub-queries
2. **Web search** — runs each sub-query through SearxNG
3. **URL scraping** — fetches and cleans full page content with Trafilatura
4. **Synthesis** — NVIDIA Nemotron-Ultra fuses all results into a structured report
5. **Citation tracking** — every claim is linked to its source URL
6. **Streaming** — all steps stream to the UI via SSE in real time

### Web Search Agent

Lightweight real-time search:
- SearxNG → top N results → LLM synthesis → streaming response
- Configurable result count and search depth
- Source URLs embedded inline in the answer

### Multi-Agent Code Squad

```
User request
    ↓
Planner Agent  →  task decomposition + subtask list
    ↓
Coder Agent    →  writes code, runs in Docker sandbox, reads output
    ↓
Reviewer Agent →  critiques, suggests improvements
    ↓
Final response →  merged, refined code delivered to user
```

All three agents stream their progress to the UI via WebSocket.

### Code Sandbox

- **Isolation** — each session gets a fresh throwaway Docker container
- **Supported runtimes** — Python, Node.js, Bash, R, Java (configurable)
- **File system** — ephemeral per session; files cleaned up on session close
- **Monaco Editor** — in-browser code editor with LSP-like features
- **Execution streaming** — stdout/stderr streamed back in real time

<br/>

---

## 👥 Real-time Collaboration

### Group Chat

- Any user can create a group and invite others via link or direct add
- The AI is always available as a participant — `@AI` to mention
- Redis pub/sub fan-out delivers messages to all connected members in under 50ms
- Message history is paginated and persistent in PostgreSQL
- Admin moderation: delete messages, remove members, archive group

### Shared Projects

- Create a project, generate a share link with configurable role
- Members see the same knowledge base, templates, and history
- File uploads go into the shared vector collection
- Permission levels: **Viewer** (read-only) · **Editor** (add files, chat) · **Admin** (manage members)

### Push Notifications

- VAPID-based web-push: works on Chrome, Firefox, Edge, Safari
- Notifications for: new group messages, project updates, billing events
- Users manage subscriptions per-device in settings
- Operators can send platform-wide broadcasts from the admin console

<br/>

---

## 💳 Billing & Subscriptions

Built-in Stripe-integrated subscription engine — no third-party billing SaaS needed.

### Plans (seeded on first boot)

| Plan | Default Features |
|------|-----------------|
| **Free** | Basic chat, limited tokens/month, no RAG |
| **Pro** | Full chat, image gen, voice, RAG, all models |
| **Teams** | Pro + group chats, shared projects, seat management |
| **Enterprise** | Teams + SSO, custom limits, SLA, dedicated support |

### Coupon Engine

- Create `PERCENT` or `FIXED` amount coupons from the admin console
- Set max redemptions, expiry dates, and plan restrictions
- Users enter codes at checkout or in subscription settings
- Stripe coupon objects are synced automatically

### Stripe Webhook Events Handled

- `customer.subscription.created` — activate plan
- `customer.subscription.updated` — handle upgrades/downgrades
- `customer.subscription.deleted` — revoke access gracefully
- `invoice.payment_succeeded` — record payment, generate PDF invoice
- `invoice.payment_failed` — notify user, start grace period
- `payment_method.attached` — update stored payment method

```bash
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
```

<br/>

---

## 🔊 Voice (STT & TTS)

### Speech-to-Text

```bash
# Cloud STT via Groq (fastest — recommended)
GROQ_API_KEY=gsk_xxxx
STT_MODEL=whisper-large-v3          # or whisper-large-v3-turbo

# Fully offline STT (no API key needed)
STT_BACKEND=local
STT_LOCAL_MODEL=large-v3            # downloaded on first use
```

### Text-to-Speech

```bash
# Unreal Speech (natural voice — recommended)
UNREAL_SPEECH_API_KEY=xxxx
TTS_VOICE=Sierra

# Edge-TTS (100% free, no API key)
TTS_BACKEND=edge-tts
TTS_EDGE_VOICE=en-US-AriaNeural     # any of 400+ voices
```

<br/>

---

## 🎨 Image Generation

```bash
# NVIDIA API — FLUX.1-Schnell
NVIDIA_API_KEY=nvapi-xxxx
IMAGE_MODEL=black-forest-labs/flux-1-schnell

# Storage
IMAGE_STORAGE_DIR=/data/images      # mapped to Docker volume
IMAGE_PURGE_AFTER_DAYS=30           # 0 = keep forever
IMAGE_GENERATION_TIMEOUT=90         # seconds before timeout
```

- Images stream to the chat via SSE
- Stored in the Docker volume `backend_images`
- Gallery view with download, share, delete
- Soft-delete then configurable hard-delete
- Inside projects: images are tagged to the project and appear in project gallery

<br/>

---

## 🛡 Security & Compliance

### Authentication

| Mechanism | Details |
|-----------|---------|
| JWT | HS256, configurable expiry, HttpOnly cookie delivery |
| Refresh Tokens | Rotation on use, immediate revocation on logout |
| bcrypt | Adaptive cost factor, resistant to GPU cracking |
| TOTP MFA | RFC 6238, compatible with any authenticator app |
| Google OAuth 2.0 | Full offline_access flow, token encryption at rest |
| GitHub OAuth | Developer sign-in |

### Network Security

| Control | Implementation |
|---------|---------------|
| Host validation | `TrustedHostMiddleware` — blocks spoofed `Host` headers |
| CORS | Strict domain allowlist, no wildcard origins |
| Rate limiting | SlowAPI + Redis sliding window per endpoint per user |
| Trusted proxy | `X-Forwarded-For` only accepted from configured CIDR ranges |
| Maintenance mode | Custom middleware: 503 with Retry-After header |

### Data Protection

| Control | Implementation |
|---------|---------------|
| Token encryption | Fernet symmetric encryption for all stored OAuth tokens |
| Soft deletion | Data is soft-deleted first; hard delete follows configurable retention window |
| GDPR consent | Affirmative consent recorded with timestamp; withdrawal supported |
| Cookie preferences | Granular per-category consent with persistent browser storage |
| Audit log | Immutable append-only log of all admin actions with actor attribution |

### AI Safety

| Layer | What it does |
|-------|-------------|
| AI Firewall | Pre-generation: screens prompt against configurable block patterns |
| Safety Scanner | Post-generation: validates model output before delivery to client |
| Supervision Service | Per-account: usage limits, quiet hours, feature restrictions |
| Content moderation | Admin-defined keyword lists + LLM-based classification |
| Admin safety panel | Real-time view of flagged content; configuration UI |

### Dependency Security (Pinned CVE-Free Versions)

| Package | Pinned Version | Vulnerabilities Fixed |
|---------|---------------|----------------------|
| `python-jose` | `3.4.0` | PYSEC-2024-233 |
| `PyJWT` | `2.13.0` | PYSEC-2025-183, PYSEC-2026-120/175/177/178/179 |

```bash
# Run CVE scan on all backend dependencies
docker compose exec backend pip-audit
```

### Code Execution Security

The Code Agent runs user code in **throwaway Docker containers** — user code never executes inside the API process. Each session gets a fresh container that is destroyed when the session ends.

> **Note:** The Docker socket mount (`/var/run/docker.sock`) required for container spawning is explicitly documented in `docker-compose.yml` with its security trade-off. For hardened production deployments, move execution to a dedicated sandbox service with the socket mount dropped from the API container.

<br/>

---

## 🖥️ Admin Console

The admin console is a fully separate React application running at `:5174`. It requires a staff or admin role — regular user accounts cannot access it.

### Pages

| Page | Capabilities |
|------|-------------|
| **Dashboard** | Real-time KPIs, DAU/MAU, revenue, active users, error rates |
| **Users** | Search, filter, impersonate, suspend, ban, erase, assign roles |
| **Analytics** | Token usage by model, endpoint latency p50/p95/p99, hourly charts |
| **API Keys** | Manage provider key pools per NVIDIA/Groq/Google/OpenRouter |
| **Models** | Hot-swap AI models without restart; per-feature model assignment |
| **Subscriptions** | All active plans, overrides, trial grants, cancellations |
| **Coupons** | Create/expire percent and fixed discount codes |
| **Billing** | Invoice history, Stripe customer links, failed payment alerts |
| **Broadcast** | Send platform-wide banners, push notifications, or emails |
| **Safety & Firewall** | Manage block patterns, review flags, set AI safety thresholds |
| **Audit Logs** | Immutable timestamped log of every admin action |
| **Platform Profile** | Legal entity, invoice branding, support contacts, social links |
| **Legal** | Manage ToS, Privacy Policy, AUP, sub-processors list |
| **System Health** | Docker service status, resource usage, queue depth |
| **Database** | Schema inspector, table browser, read-only query runner |
| **Releases** | In-app changelog editor for user-facing release notes |
| **Reports** | User-filed content reports and moderation actions |
| **Roles** | Define and assign custom RBAC roles |
| **Staff** | Internal team management with elevated permissions |
| **My Activity** | Admin's own audit history |
| **Incidents** | Status page with severity levels and timeline |

<br/>

---

## 📡 API Reference

**Interactive docs:** http://localhost:8000/docs (Swagger UI)  
**ReDoc:** http://localhost:8000/redoc

All endpoints require `Authorization: Bearer <token>` except auth endpoints.

```http
# ── Authentication ─────────────────────────────────────────────────────────
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/google
POST   /api/v1/auth/github
POST   /api/v1/auth/mfa/setup
POST   /api/v1/auth/mfa/verify
POST   /api/v1/auth/mfa/disable
POST   /api/v1/auth/password/change
POST   /api/v1/auth/password/reset-request
POST   /api/v1/auth/password/reset-confirm
DELETE /api/v1/auth/account             # GDPR erasure

# ── Chat (Server-Sent Events) ──────────────────────────────────────────────
POST   /api/v1/chat/stream              # Streaming chat completion
GET    /api/v1/chat/history             # Conversation list
GET    /api/v1/chat/{id}/messages       # Messages in conversation
DELETE /api/v1/chat/{id}               # Delete conversation
POST   /api/v1/chat/{id}/share         # Create shareable link

# ── Deep Research (SSE) ────────────────────────────────────────────────────
POST   /api/v1/research/deep            # Start deep research stream
GET    /api/v1/research/{id}/status     # Job status

# ── Web Search (SSE) ───────────────────────────────────────────────────────
POST   /api/v1/web-search/stream        # Streaming web search + synthesis

# ── RAG ───────────────────────────────────────────────────────────────────
POST   /api/v1/rag/upload               # Upload document to chat RAG
POST   /api/v1/rag/query                # Semantic query
DELETE /api/v1/rag/{file_id}            # Remove document

# ── Projects ──────────────────────────────────────────────────────────────
POST   /api/v1/projects/                # Create project
GET    /api/v1/projects/                # List user projects
GET    /api/v1/projects/{id}            # Project detail
PATCH  /api/v1/projects/{id}            # Update project
DELETE /api/v1/projects/{id}            # Delete project
POST   /api/v1/projects/{id}/knowledge  # Upload to project knowledge base
GET    /api/v1/projects/{id}/search     # Semantic search
GET    /api/v1/projects/{id}/insights   # AI-generated summary
POST   /api/v1/projects/{id}/invite     # Generate invite link
POST   /api/v1/projects/join/{token}    # Accept invite

# ── Image Generation ──────────────────────────────────────────────────────
POST   /api/v1/image/generate           # Generate image (SSE stream)
GET    /api/v1/image/gallery            # User image gallery
DELETE /api/v1/image/{id}              # Soft-delete image
GET    /api/v1/image/{id}/download      # Full-resolution download

# ── Voice ─────────────────────────────────────────────────────────────────
POST   /api/v1/voice/transcribe         # Audio file → text (STT)
POST   /api/v1/voice/synthesize         # Text → audio stream (TTS)

# ── Group Chat ────────────────────────────────────────────────────────────
POST   /api/v1/groups/                  # Create group
GET    /api/v1/groups/                  # List user groups
GET    /api/v1/groups/{id}/messages     # Message history (paginated)
POST   /api/v1/groups/{id}/members      # Add member
DELETE /api/v1/groups/{id}/members/{uid} # Remove member

# ── Connectors ────────────────────────────────────────────────────────────
GET    /api/v1/connectors/              # List available connectors
POST   /api/v1/connectors/{service}/auth     # Start OAuth flow
GET    /api/v1/connectors/{service}/callback # OAuth callback
DELETE /api/v1/connectors/{service}    # Revoke connector

# ── Subscriptions ─────────────────────────────────────────────────────────
GET    /api/v1/subscriptions/plans      # Available plans
POST   /api/v1/subscriptions/subscribe  # Subscribe to plan
POST   /api/v1/subscriptions/cancel     # Cancel subscription
POST   /api/v1/subscriptions/coupon     # Apply coupon

# ── Notifications ─────────────────────────────────────────────────────────
GET    /api/v1/notifications/           # User notification list
POST   /api/v1/notifications/push/subscribe   # Register push subscription
DELETE /api/v1/notifications/{id}       # Mark read / dismiss

# ── Consent & Legal ───────────────────────────────────────────────────────
POST   /api/v1/consent/record           # Record consent
GET    /api/v1/consent/status           # Current consent state
DELETE /api/v1/consent/withdraw         # Withdraw consent

# ── WebSockets ────────────────────────────────────────────────────────────
WS     /ws/chat/{session_id}            # Real-time chat
WS     /ws/groups/{group_id}            # Group chat fan-out
WS     /ws/code/{session_id}            # Code agent stream
WS     /ws/agent/{session_id}           # Multi-agent squad stream

# ── Admin ─────────────────────────────────────────────────────────────────
GET    /api/v1/admin/users              # User list + filters
GET    /api/v1/admin/analytics          # Platform analytics
GET    /api/v1/admin/audit              # Audit log (immutable)
POST   /api/v1/admin/broadcast          # Platform broadcast
GET    /api/v1/admin/health             # Detailed system health

# ── Observability ─────────────────────────────────────────────────────────
GET    /health                          # Service health check
GET    /metrics                         # Prometheus metrics
```

<br/>

---

## 📊 Observability

Built-in Prometheus metrics at `/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `infichat_active_ws_connections` | Gauge | Active WebSocket connections by room |
| `infichat_tokens_total` | Counter | Tokens used by model, provider, user |
| `infichat_request_duration_seconds` | Histogram | Endpoint latency (p50/p95/p99) |
| `infichat_background_task_queue_depth` | Gauge | Background task queue depth |
| `infichat_cache_hits_total` | Counter | Redis cache hits |
| `infichat_cache_misses_total` | Counter | Redis cache misses |
| `infichat_errors_total` | Counter | Errors by endpoint and status code |
| `infichat_image_generations_total` | Counter | Image generation requests |
| `infichat_rag_queries_total` | Counter | RAG query count by collection |

<br/>

---

## 🌐 Production Deployment

### Recommended Stack

```
Internet
    │
    ▼
Cloudflare (DDoS, WAF, TLS)
    │
    ▼
nginx / Traefik (reverse proxy, TLS termination)
    ├── /          → frontend-new   :5173
    ├── /admin     → admin-frontend :5174
    └── /api       → backend        :8000
```

### Production `.env` Hardening

```bash
# Generate strong secrets
SECRET_KEY=$(openssl rand -hex 64)
CONNECTOR_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Use managed database and Redis
DATABASE_URL=postgresql+psycopg2://user:pass@managed-pg.internal:5432/infichat
REDIS_URL=rediss://user:pass@managed-redis.internal:6380/0

# Your domain
PUBLIC_BASE_URL=https://chat.yourdomain.com
ALLOWED_HOSTS=chat.yourdomain.com,admin.yourdomain.com

# Generate VAPID keys once — never rotate without re-registering push subscriptions
docker compose exec backend python -c "from pywebpush import generate_vapid_keys; k = generate_vapid_keys(); print(k)"
```

### LAN / On-Premise

```cmd
rem Windows: add your LAN IP to ALLOWED_HOSTS automatically
docker-manage.bat → [8] Enable phone/LAN access
```

<br/>

---

## 🧪 Testing

```bash
# Full backend test suite
docker compose exec backend pytest

# Skip slow integration tests
docker compose exec backend pytest -m "not slow"

# With HTML coverage report
docker compose exec backend pytest --cov=app --cov-report=html

# Lint (ruff — zero tolerance)
docker compose exec backend ruff check .

# Type check (mypy)
docker compose exec backend mypy app/

# Frontend type check
cd Frontend-New && npx tsc --noEmit

# Frontend lint
cd Frontend-New && npm run lint

# Dependency CVE scan
docker compose exec backend pip-audit
```

<br/>

---

## 🗺️ Roadmap

| Status | Feature |
|--------|---------|
| 🔄 In Progress | LiteLLM proxy — unified entry point for all providers |
| 🔄 In Progress | MCP server support — Model Context Protocol tool registry |
| 📋 Planned | Plugin marketplace — installable prompt-and-tool bundles |
| 📋 Planned | Multi-tenant workspaces — full org-level isolation |
| 📋 Planned | Desktop app — Electron wrapper (Windows / macOS / Linux) |
| 📋 Planned | Mobile app — React Native (iOS + Android) |
| 📋 Planned | Kubernetes Helm chart — production-grade k8s deployment |
| 📋 Planned | LLM evaluation suite — A/B test models per feature with automated scoring |
| 📋 Planned | Fine-tuning pipeline — PEFT/LoRA integration for custom model adaptation |
| 📋 Planned | SAML / SSO — enterprise identity provider support (Okta, Azure AD) |
| 📋 Planned | Streaming RAG — real-time document ingestion without re-indexing |
| 📋 Planned | Multi-modal image input in group chat |
| 📋 Planned | Scheduled agents — cron-triggered autonomous workflows |

<br/>

---

## 🤝 Contributing

We welcome contributions that improve the documentation, configuration templates, test infrastructure, or open-source components of InfiChat.

### Local Development Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Fill in: DATABASE_URL, REDIS_URL, NVIDIA_API_KEY

# Apply migrations
alembic upgrade head

# Start dev server (hot reload)
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd Frontend-New
npm install
npm run dev                       # → http://localhost:5173

# Admin (separate terminal)
cd admin-frontend
npm install
npm run dev                       # → http://localhost:5174
```

### Pull Request Checklist

- [ ] `ruff check .` passes with zero errors
- [ ] `pytest` test suite passes
- [ ] `npx tsc --noEmit` passes (no TypeScript errors)
- [ ] No secrets, API keys, or real credentials in the diff
- [ ] New environment variables documented in the relevant `.env.example`
- [ ] Alembic migration added if any SQLAlchemy model was changed
- [ ] `pip-audit` shows no new CVEs introduced

<br/>

---

## 📜 License

```
Copyright (c) 2026 Bhavith Guguloth. All rights reserved.

InfiChat is proprietary software. A limited license is granted
to individuals and organizations for personal or internal use only.

Commercial use, redistribution, public SaaS hosting, white-labeling,
and sublicensing require a separate written commercial agreement.
```

See the full **[LICENSE](LICENSE)** file for complete terms, restrictions,  
warranty disclaimers, and governing law.

For commercial licensing inquiries:  
📧 **gugulothubhavith@gmail.com**

<br/>

---

## 🙏 Acknowledgements

InfiChat is built on the shoulders of exceptional open-source projects:

| Project | Role in InfiChat |
|---------|-----------------|
| [FastAPI](https://fastapi.tiangolo.com) | Backend ASGI framework |
| [TanStack Router](https://tanstack.com/router) | Type-safe frontend routing |
| [TanStack Query](https://tanstack.com/query) | Server state management |
| [shadcn/ui](https://ui.shadcn.com) | Component primitives |
| [Radix UI](https://radix-ui.com) | Accessible UI foundations |
| [Framer Motion](https://framer.com/motion) | Animations & transitions |
| [ChromaDB](https://trychroma.com) | Vector database |
| [FAISS](https://github.com/facebookresearch/faiss) | Local vector search fallback |
| [SearxNG](https://searxng.org) | Privacy-first web search |
| [Unstructured](https://unstructured.io) | Document parsing + OCR |
| [faster-whisper](https://github.com/guillaumekln/faster-whisper) | Local speech-to-text |
| [Trafilatura](https://trafilatura.readthedocs.io) | Web content extraction |
| [Playwright](https://playwright.dev) | Browser automation |
| [SQLAlchemy](https://sqlalchemy.org) | Python ORM |
| [Alembic](https://alembic.sqlalchemy.org) | Database migrations |
| [Pydantic](https://docs.pydantic.dev) | Data validation |
| [Stripe](https://stripe.com) | Payment processing |
| [Monaco Editor](https://microsoft.github.io/monaco-editor) | In-browser code editor |
| [Zustand](https://github.com/pmndrs/zustand) | Lightweight state management |
| [tiktoken](https://github.com/openai/tiktoken) | Accurate token counting |

<br/>

---

<div align="center">

<br/>

**InfiChat — AI Chat Platform · Built with ❤️ · Your data, your rules**

<br/>

[![GitHub stars](https://img.shields.io/github/stars/gugulothubhavith/Chatbot-InfiChat?style=for-the-badge&logo=github&color=gold)](https://github.com/gugulothubhavith/Chatbot-InfiChat/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/gugulothubhavith/Chatbot-InfiChat?style=for-the-badge&logo=github&color=blue)](https://github.com/gugulothubhavith/Chatbot-InfiChat/network/members)
[![GitHub issues](https://img.shields.io/github/issues/gugulothubhavith/Chatbot-InfiChat?style=for-the-badge&logo=github&color=red)](https://github.com/gugulothubhavith/Chatbot-InfiChat/issues)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](LICENSE)

<br/>

*© 2026 Bhavith Guguloth · InfiChat™ is a registered trademark · All rights reserved.*

</div>
