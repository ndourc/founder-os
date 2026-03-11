# Founder OS - AI Operational Intelligence Platform

Founder OS is an **AI-powered operational intelligence system** that transforms raw meeting notes into a structured execution engine inside Notion.

Instead of letting decisions disappear inside meeting documents, Founder OS automatically extracts tasks, detects duplicates, stores strategic insights, computes project health metrics, and generates an executive briefing - all from a single command.

Founder OS acts like a lightweight **AI Chief Operating Officer**, ensuring that conversations turn into trackable work and that founders always have visibility into execution, risk, and priorities.

---

## Table of Contents

- [Motivation](#motivation)
- [What Makes Founder OS Interesting](#what-makes-founder-os-interesting)
- [Key Capabilities](#key-capabilities)
- [Who It's For](#whos-it-for)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Notion Database Schema](#notion-database-schema)
- [Module Reference](#module-reference)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
- [AI Providers & Fallback Chain](#ai-providers--fallback-chain)
- [Possible Integrations](#possible-integrations)
- [Roadmap](#roadmap)

---

## Motivation

In early-stage startups, the biggest operational challenge is not a lack of ideas - it is **losing track of execution**.

Important discussions happen in meetings. Decisions are made. Tasks are mentioned. Strategic insights emerge. But after the meeting ends, much of that information becomes fragmented:

- Tasks remain buried inside meeting notes
- Insights get forgotten
- Priorities become unclear
- Projects lose visibility

Large companies solve this with operations teams, project managers, and structured reporting systems. Early-stage startups rarely have that luxury.

Founder OS was built to solve this problem. The goal is simple:

> **Turn conversations into execution automatically.**

Instead of manually converting meeting notes into tasks, tracking insights, and compiling status updates, Founder OS performs that work automatically and maintains a structured operational layer inside Notion - transforming it from a passive note-taking tool into an **active operational intelligence system**.

---

## What Makes Founder OS Interesting

Founder OS is not just a meeting summariser. It is designed as a **complete operational pipeline**.

From a single input - meeting notes in plain text - the system:

1. Extracts structured meeting information using LLMs
2. Creates and links tasks to projects and meetings
3. Detects duplicate tasks using fuzzy string similarity
4. Stores strategic insights in a long-term knowledge base
5. Computes project health and execution risk metrics
6. Generates an AI-written daily executive briefing

This allows founders to run a meeting and instantly produce a **living operational record** of what happened, what needs to be done, and what risks are emerging - without writing a single Notion page manually.

---

## Key Capabilities

### 1. Meeting Intelligence

Automatically extracts from raw notes:

- Meeting title and date
- Attendees
- Associated project
- Action items with owners and priorities
- Strategic decisions as structured insights

### 2. Automatic Task Generation

Every extracted task is automatically:

- Added to the Tasks database in Notion
- Linked to the originating meeting
- Linked to the correct project
- Assigned a priority level (High / Medium / Low)

**Duplicate task detection** is run before creation - if a similar task already exists, the meeting is linked to the existing task instead of creating clutter.

### 3. Founder Memory (Strategic Knowledge Base)

Strategic insights from meetings are captured in a dedicated **Founder Memory** database, creating a searchable institutional knowledge base of decisions and observations across time. Insights are categorised and assigned confidence scores (1–5) so founders can quickly revisit key moments of strategic thinking.

### 4. Project Health Analytics

Founder OS continuously computes operational metrics across all projects:

- Total, completed, overdue, and high-priority task counts
- Project progress percentage (0–100)
- Execution risk level (High / Medium / Low)

These metrics are written back to Notion automatically after every pipeline run.

### 5. Founder Daily Briefing

At the end of each run, Founder OS generates an **AI-written daily executive briefing** that surfaces:

- Open task counts across the workspace
- High-priority and overdue work
- Projects at risk
- Top operational priorities

The goal is to give founders the **same situational clarity that an operations lead or COO would normally provide**.

---

## Who's It For

| User                                   | Why They Need It                                                                        |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| **Solo founders**                      | No ops team - needs one command to turn a meeting into tracked execution                |
| **Early-stage startups (2–15 people)** | Too small for a full-time COO but still need operational structure                      |
| **Technical co-founders**              | Already live in terminals and Notion; want automation without bloated SaaS tools        |
| **Notion power users**                 | Use Notion as their single source of truth; need a smart engine behind it               |
| **Accelerator / incubator cohorts**    | Multiple founders needing a standardised system for tracking decisions and progress     |
| **Fractional COOs / operators**        | Managing multiple portfolio companies and needing automated meeting-to-action pipelines |

---

## How It Works

```
Meeting Notes (plain text)
        │
        ▼
┌───────────────────┐
│   LLM Extractor   │  ← Gemini 2.5 Flash / GPT-4o-mini / Rule-based fallback
└───────────────────┘
        │
        ▼  Structured JSON:
        │  { title, date, attendees, project, tasks[], insights[] }
        │
   ┌────┴────────────────────────────────────────┐
   │                                             │
   ▼                                             ▼
Project (find or create)               Meeting Page (created)
   │                                             │
   └──────────────┬──────────────────────────────┘
                  │
                  ▼
           Tasks (deduplication check)
           ├── Duplicate? → Link meeting to existing task
           └── New? → Create task, link to meeting + project
                  │
                  ▼
         Strategic Insights → Founder Memory DB
                  │
                  ▼
         Analytics Engine → Project metrics written back to Notion
                  │
                  ▼
         Founder Daily Briefing (AI-generated summary → Briefings DB)
```

---

## Architecture

```
notion-hack/
├── main.py                  Entry point - orchestrates the full pipeline
├── config.py                Loads env vars, initialises API clients
├── llm_extractor.py         Calls LLM, parses + normalises structured JSON
├── notion_meetings.py       Creates Meeting pages in Notion
├── notion_tasks.py          Creates Task pages in Notion
├── notion_projects.py       Finds or creates Project pages in Notion
├── notion_memory.py         Stores strategic insights in Founder Memory DB
├── notion_briefings.py      Generates and writes Founder Daily Briefing
├── analytics_engine.py      Computes per-project metrics, writes to Notion
├── task_similarity.py       Fuzzy deduplication before task creation
└── requirements.txt         Python dependencies
```

---

## Notion Database Schema

The pipeline reads from and writes to five Notion databases.

### Tasks

| Property | Type     | Notes                      |
| -------- | -------- | -------------------------- |
| Task     | title    | Task name                  |
| Status   | status   | To do / In progress / Done |
| Priority | select   | High / Medium / Low        |
| Meeting  | relation | Source meeting             |
| Project  | relation | Parent project             |
| Date     | date     | Due date (optional)        |

### Meetings

| Property             | Type      | Notes                                       |
| -------------------- | --------- | ------------------------------------------- |
| Title of the meeting | title     | AI-extracted title                          |
| Date                 | date      | Meeting date (YYYY-MM-DD)                   |
| Attendees            | rich_text | Comma-separated names                       |
| Full notes           | rich_text | Raw meeting notes (truncated at 2000 chars) |

### Projects

| Property            | Type     | Notes                       |
| ------------------- | -------- | --------------------------- |
| Project Name        | title    | Project identifier          |
| Meetings            | relation | Linked meetings             |
| Tasks               | relation | Linked tasks                |
| Total Tasks         | number   | Written by analytics engine |
| Completed Tasks     | number   | Written by analytics engine |
| Overdue Tasks       | number   | Written by analytics engine |
| High Priority Tasks | number   | Written by analytics engine |
| Progress Percentage | number   | 0–100                       |
| Risk Level          | select   | High / Medium / Low         |

### Founder Memory

| Property        | Type     | Notes                                                       |
| --------------- | -------- | ----------------------------------------------------------- |
| Insight         | title    | Short, punchy insight title                                 |
| Category        | select   | Strategy / Product / Growth / Operations / Hiring / Finance |
| Confidence      | number   | 1 (low) to 5 (high)                                         |
| Created At      | date     | Auto-set to today                                           |
| Source Meeting  | relation | The meeting this came from                                  |
| Related Project | relation | Associated project                                          |

### Founder Briefings

| Property            | Type      | Notes                                |
| ------------------- | --------- | ------------------------------------ |
| Briefing Title      | title     | e.g. "Founder Briefing – 2026-03-11" |
| Date                | date      | Briefing date                        |
| Open Tasks          | number    | Workspace-wide count                 |
| High Priority Tasks | number    | Workspace-wide count                 |
| Overdue Tasks       | number    | Workspace-wide count                 |
| Projects At Risk    | number    | Count of High/Medium risk projects   |
| Summary             | rich_text | AI-generated executive summary       |
| Top Priorities      | rich_text | High-priority open tasks list        |
| Linked Projects     | relation  | All active projects                  |

---

## Module Reference

### `main.py`

Entry point. Reads meeting notes from a file path argument, stdin, or the built-in demo. Calls `extract_meeting_and_tasks`, then `push_meeting_and_tasks_to_notion` which sequences the full 8-step pipeline.

### `config.py`

Reads all secrets and IDs from `.env`. Initialises `notion`, `openai_client`, and `gemini_client`. Exposes `OPENAI_TIMEOUT_SEC = 30`.

### `llm_extractor.py`

Three-tier extraction fallback:

1. **OpenAI** (gpt-4o-mini, with 30s timeout)
2. **Gemini** (gemini-2.5-flash-lite, with 429 retry logic)
3. **Rule-based** (regex + line-by-line parsing, always succeeds)

Uses a minimal token-saving prompt. Returned compact keys (`t`, `d`, `a`, `p`, `pr`) are normalised back to full field names by `_map_to_standard_format` before any downstream module sees the data.

### `task_similarity.py`

Uses `difflib.SequenceMatcher` to compare a new task title against all existing tasks. Threshold of **0.82** triggers a duplicate match. On match, the pipeline links the current meeting to the existing task instead of creating a new one.

### `analytics_engine.py`

- `compute_project_metrics(project_id)` - fetches all tasks for a project and computes total, completed, overdue, high-priority counts, progress %, and a risk score.
- `_assess_risk(...)` - returns `High / Medium / Low` based on weighted signals (overdue count, high-priority count, low completion rate).
- `compute_and_write_all_project_metrics()` - iterates all projects, computes, and writes metrics back to Notion.
- `get_workspace_task_counts()` - returns aggregate open/high-priority/overdue counts across all tasks.

### `notion_briefings.py`

Generates a prose executive summary using OpenAI → Gemini → rule-based template fallback. Appends risk warnings. Creates a page in the Founder Briefings DB with all KPI numbers, the AI summary, and a top-priorities list.

### `notion_memory.py`

Takes the `insights` array from the LLM extractor and creates one Notion page per insight in the Founder Memory DB. Categories are normalised to the six valid options. Confidence is clamped to 1–5.

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- A Notion workspace with an [Internal Integration](https://www.notion.so/my-integrations) token
- The five Notion databases created and shared with your integration
- At least one of: OpenAI API key or Gemini API key

### Install

```bash
git clone https://github.com/ndourc/founder-os.git
cd founder-os
python -m venv ntn_env
source ntn_env/Scripts/activate   # Windows
# source ntn_env/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

```env
NOTION_TOKEN=secret_...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIzaSy...

TASKS_DATABASE_ID=...
TASKS_DATA_SOURCE=...
MEETINGS_DATABASE_ID=...
PROJECTS_DATABASE_ID=...
PROJECTS_DATA_SOURCE=...
MEETINGS_DATA_SOURCE=...
FOUNDER_MEMORY_DATABASE_ID=...
FOUNDER_MEMORY_DATA_SOURCE=...
FOUNDER_BRIEFINGS_DATABASE_ID=...
FOUNDER_BRIEFINGS_DATA_SOURCE=...
```

> **How to get Data Source IDs:** Each Notion database has one or more data sources. Retrieve a database via `notion.databases.retrieve(database_id=...)` - the `data_sources[0]['id']` field is your data source ID.

---

## Configuration

| Variable                        | Required | Description                           |
| ------------------------------- | -------- | ------------------------------------- |
| `NOTION_TOKEN`                  | Yes      | Internal integration token            |
| `OPENAI_API_KEY`                | Optional | Primary LLM provider                  |
| `GEMINI_API_KEY`                | Optional | Fallback LLM provider                 |
| `TASKS_DATABASE_ID`             | Yes      | For creating task pages               |
| `TASKS_DATA_SOURCE`             | Yes      | For querying tasks                    |
| `MEETINGS_DATABASE_ID`          | Yes      | For creating meeting pages            |
| `PROJECTS_DATABASE_ID`          | Yes      | For creating project pages            |
| `PROJECTS_DATA_SOURCE`          | Yes      | For querying all projects             |
| `FOUNDER_MEMORY_DATABASE_ID`    | Yes      | For storing insights                  |
| `FOUNDER_BRIEFINGS_DATABASE_ID` | Yes      | For writing daily briefings           |
| All `*_DATA_SOURCE` IDs         | Yes      | For Notion's `data_sources` query API |

---

## Running the Pipeline

```bash
# Built-in demo notes
python main.py

# From a text file
python main.py meeting_notes.txt

# From stdin (pipe)
cat my_notes.txt | python main.py

# From stdin (interactive)
python main.py < my_notes.txt
```

### Expected output

```
No input provided - running with built-in demo notes.
────────────────────────────────────────────
...notes displayed...
────────────────────────────────────────────

Extracting details from meeting notes …
provider: Gemini ✔
Extracted Meeting: Q3 Marketing & Growth Sync
Extracted 4 task(s), 3 insight(s)

Checking for project 'Project Titan Launch' …
  + Creating new project: Project Titan Launch
Creating meeting page in Notion …
  ✔ Meeting Created: Q3 Marketing & Growth Sync
    https://www.notion.so/...

Pushing tasks to Notion …
  ✔ Created  [High]  Finalize LinkedIn ad copy
  ✔ Created  [Medium]  Draft outbound sales email sequence
  ...

Storing 3 strategic insight(s) …
  ✔ [Strategy] Shift Q3 budget to LinkedIn (confidence: 4/5)
  ...

Computing project analytics …
  🟢 Project Titan Launch: 0/4 tasks (0%)  Risk: Low
  ✔ Updated 1 project(s).

Generating 'Founder Briefing – 2026-03-11' …
  ✔ Briefing created: https://www.notion.so/...
```

---

## AI Providers & Fallback Chain

```
               Meeting Notes
                    │
         ┌──────────▼──────────┐
         │    OpenAI (primary) │  gpt-4o-mini, temp=0.2, timeout=30s
         └──────────┬──────────┘
          on error  │  (429, timeout, quota exceeded)
         ┌──────────▼──────────┐
         │   Gemini (fallback) │  gemini-2.5-flash-lite, 429 auto-retry
         └──────────┬──────────┘
          on error  │
         ┌──────────▼──────────┐
         │  Rule-based parser  │  regex + line-by-line, always succeeds
         └─────────────────────┘
```

The briefing summary uses the same fallback chain independently from the extraction.

---

## Possible Integrations

### Communication & Scheduling

| Tool                        | Integration Idea                                                                      |
| --------------------------- | ------------------------------------------------------------------------------------- |
| **Slack**                   | Slash command `/founder-os [notes]` or post to a channel to auto-trigger the pipeline |
| **Google Meet / Zoom**      | Webhook on meeting end → transcript fed as `meeting_notes`                            |
| **Otter.ai / Fireflies.ai** | Auto-export transcript → pipe into `python main.py` via webhook                       |
| **Google Calendar**         | Post-meeting trigger using Google Calendar webhooks and Apps Script                   |
| **Microsoft Teams**         | Teams bot that listens for meeting transcripts and submits them                       |

### CRM & Sales

| Tool           | Integration Idea                                                                       |
| -------------- | -------------------------------------------------------------------------------------- |
| **HubSpot**    | Sync extracted tasks with HubSpot deals/contacts; create follow-up tasks automatically |
| **Salesforce** | Map `project_name` to Salesforce Opportunities; write meeting outcomes to Activity log |
| **Pipedrive**  | Create activities and notes from extracted meeting data                                |

### Project & Engineering

| Tool       | Integration Idea                                                                |
| ---------- | ------------------------------------------------------------------------------- |
| **Linear** | Create Linear issues from extracted tasks alongside Notion tasks                |
| **Jira**   | Post tasks to a Jira project board via REST API                                 |
| **GitHub** | Create GitHub Issues from technical tasks; link commits back to Notion meetings |
| **Asana**  | Parallel task creation in Asana for teams that prefer it                        |

### Data & Analytics

| Tool              | Integration Idea                                                              |
| ----------------- | ----------------------------------------------------------------------------- |
| **Google Sheets** | Export project metrics and briefing summaries to a live spreadsheet dashboard |
| **Looker Studio** | Connect to the Sheets export for visual KPI dashboards                        |
| **Metabase**      | Query Notion's internal structure (via export) for custom analytics           |

### Automation & Orchestration

| Tool                           | Integration Idea                                                                        |
| ------------------------------ | --------------------------------------------------------------------------------------- |
| **Zapier / Make (Integromat)** | Trigger the pipeline from any app event (new email, form submission, calendar event)    |
| **n8n**                        | Self-hosted workflow automation to chain meeting transcripts → Founder OS → Slack alert |
| **GitHub Actions**             | Schedule `python main.py notes.txt` as a cron job; commit notes to repo to trigger      |
| **AWS Lambda / GCP Cloud Run** | Host the pipeline as a serverless function triggered by S3 uploads or Pub/Sub events    |

### Input Sources

| Source                  | Integration Idea                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------- |
| **Email**               | Forward meeting summary emails to a parsing address that calls the pipeline           |
| **WhatsApp / Telegram** | Bot that accepts voice notes or text, transcribes, and pipes into the pipeline        |
| **Notion itself**       | A "Submit Notes" button block in Notion that calls a webhook pointing at the pipeline |
| **Voice (Whisper)**     | Add OpenAI Whisper as a pre-processing step to accept audio recordings as input       |

---

## Roadmap

- **Web UI** - Simple Flask/FastAPI frontend to paste notes and watch results appear in real time
- **Webhook endpoint** - Deploy as an API so any tool can POST meeting notes and get back a Notion URL
- **Multi-workspace support** - Config per team/client with separate `.env` profiles
- **Confidence-gated insights** - Only store insights above a configurable confidence threshold
- **Web UI** - Flask/FastAPI frontend to paste notes and see results populate in real time
- **Webhook endpoint** - Deploy as an API so any tool can POST meeting notes and receive a Notion URL
- **Slack / email briefing digest** - Push the daily briefing to Slack or email at a scheduled time
- **Voice input** - Whisper transcription as a pre-processing step before extraction
- **Recurring meeting detection** - Auto-link recurring meeting titles to the same project
- **OKR tracking** - Map strategic insights to OKR goals stored in a dedicated Notion DB
- **Confidence-gated insights** - Only store insights above a configurable confidence threshold
- **Multi-workspace support** - Per-client `.env` profiles for fractional operators
- **Multi-language support** - Translation step before extraction for non-English meeting notes

---

## Final Thought

Founder OS is designed to help startups maintain operational clarity without adding operational overhead.

Instead of manually organising work after every meeting, founders can focus on what matters most - **building the company**.

> Conversation → Structure → Execution → Insight
