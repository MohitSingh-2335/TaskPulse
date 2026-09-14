# ⚡ TaskPulse: Project Merge & Rebranding Blueprint

> Master specification documenting the synthesis of **Dynamic-Daily-Task-Engine** and **Observable-local-ai** into a unified, privacy-first productivity OS.

---

## 🏷️ 1. Unified Identity & GitHub Target

* **Project Name**: **TaskPulse: Dynamic Task Engine with Local AI & Observability**
* **GitHub Repo Name**: `Dynamic-Daily-Task-Engine` (or `TaskPulse-AI`)
* **GitHub Repository URL**: `https://github.com/MohitSingh-2335/Dynamic-Daily-Task-Engine`
* **Short Description / About**: 
  > *Self-hosted, privacy-first task automation engine powered by local LLM classification, voice inbox, Google Calendar sync, and real-time telemetry observability.*
* **Topic Tags**: `fastapi`, `local-ai`, `opentelemetry`, `task-automation`, `google-calendar-api`, `productivity`, `privacy-first`, `python`

---

## 🔍 2. Analysis of the Two Original Projects

### Project A: `Dynamic-Daily-Task-Engine` (The Productivity Backbone)
* **Origins**: Personal automation engine for daily task scheduling.
* **Core Strengths**:
  * Google OAuth2 authentication & Calendar REST API synchronization.
  * Modular inboxes: voice recordings, quick ideas, and REST task intake.
  * SQLite database with automated migration and schema initialization.
* **Limitations Before Merge**: Lacked automated intelligent prioritization and real-time service health telemetry.

### Project B: `Observable-local-ai` (The Intelligence & Telemetry Suite)
* **Origins**: Local model inference and observability research repo.
* **Core Strengths**:
  * Structured OpenTelemetry-style latency metrics and request tracing.
  * Local model execution pipeline without external API dependencies.
  * Unit and integration test suite (`tests/`) verifying model contracts.
* **Limitations Before Merge**: Disconnected microservice without an active user-facing application consuming its inferences.

---

## ⚡ 3. The Combined Result: What It Becomes

By integrating `Observable-local-ai` into `Dynamic-Daily-Task-Engine/local_ai/`:
1. **100% Private Task Intelligence**: Raw voice memos and private daily notes are evaluated locally on your laptop without sending sensitive personal data to OpenAI or Google cloud.
2. **Context-Aware Dynamic Scheduling**: The local model parses notes, extracts deadlines, computes priority scores, and schedules calendar events.
3. **Embedded Observability**: Every engine cycle, transcription latency, and sync event is tracked with telemetry metrics for rock-solid reliability.

---

## 🛠️ 4. GitHub Renaming & Sync Instructions

1. **Clean Up Old Repo on GitHub**:
   * Navigate to `https://github.com/MohitSingh-2335/Observable-local-ai/settings`.
   * Scroll down to **Danger Zone** -> **Delete this repository** (since 100% of its code and tests now live inside `Dynamic-Daily-Task-Engine/local_ai/`).
2. **Update Dynamic-Daily-Task-Engine on GitHub**:
   * Update the GitHub description and topic tags per Section 1 above.
3. **Commit & Push Local Changes**:
   ```bash
   cd d:\Project\Dynamic-Daily-Task-Engine
   git add .
   git commit -m "feat: integrate local AI intelligence and telemetry observability suite"
   git push origin main
   ```
