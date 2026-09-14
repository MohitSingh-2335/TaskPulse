# ⚡ TaskPulse: Dynamic Task Engine with Local AI & Observability

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![Storage](https://img.shields.io/badge/Storage-SQLite%20%7C%20Supabase-emerald.svg)]()
[![AI](https://img.shields.io/badge/AI-Local%20%7C%20Groq%20Fallback-violet.svg)]()
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

> **TaskPulse** is a self-hosted, privacy-first, zero-cost task automation engine and productivity operating system. It bridges the gap between unstructured thought capture (voice memos, brain dumps, fleeting ideas) and disciplined calendar execution (time-blocking, priority ranking, evening review, and rollover).

---

## 🌟 Key Highlights

- 🧠 **Zero-Cost & Local-First Intelligence**: Operates 100% locally with an embedded SQLite database (`data/task_engine.db`) and smart offline heuristic task parser. Supports Local Ollama and Groq Cloud API (`llama-3.3-70b-versatile`) free-tier as optional AI providers.
- 🎨 **Modern Glassmorphic Web Dashboard**: Single-page dark-mode web application featuring real-time speech dictation, visual timeline scheduling, interactive task checklists, and an evening review hub.
- 📅 **Intelligent Google Calendar Time-Blocking**: Automatically organizes tasks for tomorrow starting at 07:00 AM with custom buffer intervals. Flags high-priority focus items as `[Deep Work]` with color highlights.
- 🌙 **Evening Review & Rollover Engine**: Walk through your day's scheduled tasks, mark completed items, or roll over unfinished work with custom remaining minutes.
- 💡 **Idea Staging Inbox**: Instantly capture fleeting thoughts and convert them into structured multi-step task plans with one click.
- 📊 **Real-Time Telemetry & Observability**: Integrated performance observability tracking AI inference latency (ms), token metrics, and operational health.

---

## 🏗️ Architecture

```text
+-----------------------------------------------------------------------------------+
|                                TASKPULSE SYSTEM                                   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Web UI Dashboard ]   <----->  [ REST API Layer ]  <----->  [ Task Service ]    |
|  - Brain Dump Intake             - Flask Endpoints            - Hierarchy Engine  |
|  - Voice Dictation               - CORS Enabled               - Slot Calculator   |
|  - Calendar Timeline             - Health / Readiness         - Review / Rollover |
|  - Evening Review Hub                                                             |
|  - Telemetry Dashboard                                                            |
|                                                                                   |
+---------------------------+-----------------------------------+-------------------+
                            |                                   |
                            v                                   v
             [ Local AI & Observability ]              [ Dual-Mode Storage ]
             - Local LLM / Ollama                      - Local SQLite (Default)
             - Groq Free-Tier Fallback                 - Zero-cost & offline
             - Rule-based Heuristic Fallback           - Supabase PostgreSQL
             - Telemetry Logger (Latency, Tokens)      - Cloud sync if active
                            |                                   |
                            +-----------------+-----------------+
                                              |
                                              v
                                   [ External Integrations ]
                                   - Google Calendar API (v3)
                                   - Google OAuth2 Flow
+-----------------------------------------------------------------------------------+
```

---

## 📁 Repository Structure

```text
Dynamic-Daily-Task-Engine/
├── .env.example                # Safe environment variable template
├── .gitignore                  # Robust security & secret ignore rules
├── README.md                   # Documentation & setup guide
├── requirements.txt            # Core dependencies
├── run.py                      # Main launcher (starts Web Dashboard & API)
├── docs/                       # Architecture & documentation
│   ├── ARCHITECTURE.md         # Full architecture specification
│   ├── TASK_ENGINE_MERGE_BLUEPRINT.md # Master merge specification
│   └── schema.sql              # Database schema (SQLite & PostgreSQL)
├── src/                        # Modular source code
│   ├── app.py                  # Flask App factory & dashboard router
│   ├── config.py               # Centralized configuration & auto .env loader
│   ├── core/                   # Domain services & integrations
│   │   ├── database.py         # SQLite & Supabase dual-storage adapter
│   │   ├── task_service.py     # Scheduling, priority, and rollover logic
│   │   └── calendar_sync.py    # Google Calendar OAuth & event syncing
│   ├── local_ai/               # Local AI & Observability suite
│   │   ├── engine.py           # Unified inference (Ollama / Groq / Heuristic)
│   │   ├── parser.py           # Structured JSON plan extraction
│   │   ├── voice.py            # Audio transcription handler
│   │   └── telemetry.py        # Latency, token, and health tracking
│   ├── api/                    # REST API routes
│   │   ├── routes_tasks.py     # Task, review, idea, and schedule endpoints
│   │   └── routes_ai.py        # Intake and telemetry endpoints
│   └── web/                    # Modern Web Dashboard
│       ├── templates/
│       │   └── index.html      # Responsive dashboard SPA
│       └── static/
│           ├── css/style.css   # Dark glassmorphism design system
│           └── js/app.js       # Voice dictation, timeline, and review logic
└── tests/                      # Automated test suite
    ├── test_database.py        # Database CRUD & schema tests
    ├── test_task_service.py    # Scheduling math & rollover tests
    ├── test_ai_parser.py       # JSON extraction & heuristic parser tests
    └── test_api.py             # Full REST API integration tests
```

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/MohitSingh-2335/Dynamic-Daily-Task-Engine.git
cd Dynamic-Daily-Task-Engine
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*Note: By default, TaskPulse uses the zero-cost local SQLite database and offline rule-based parser without requiring any external keys.*

If you want cloud LLM acceleration or Google Calendar sync:
- Set `GROQ_API_KEY` in `.env` for free fast inference.
- Place `credentials.json` (from Google Cloud Console OAuth Desktop App) in the root directory to sync with Google Calendar.

### 4. Launch TaskPulse
Start the application:
```bash
python run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

Run the full automated test suite (database, services, AI parsers, REST endpoints):
```bash
python -m pytest tests/ -v
```
All 16 tests verify schema migration, schedule calculations, rollover increments, and API contracts.

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web Dashboard Interface |
| `GET` | `/api/health` | Health check & service status |
| `GET` | `/api/readiness` | Database storage & calendar connection readiness |
| `POST` | `/api/intake` | Converts unstructured text into structured goals and tasks |
| `POST` | `/api/plan` | Directly creates a goal and task plan |
| `GET` | `/api/status` | Returns a snapshot of scheduled, pending, and completed tasks |
| `POST` | `/api/schedule` | Time-blocks pending tasks and syncs with Google Calendar |
| `GET` | `/api/review` | Fetches tasks scheduled for today |
| `POST` | `/api/review` | Applies completion or rollover updates |
| `GET` | `/api/ideas` | Lists unread ideas from the idea inbox |
| `POST` | `/api/ideas` | Captures a quick idea |
| `GET` | `/api/telemetry` | Returns AI latency, token usage, and observability logs |

---

## 📄 License
This project is open-source under the MIT License.
