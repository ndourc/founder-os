"""
Notion Briefings - Feature 1
==============================
Generates and writes a Founder Daily Briefing to the Founder Briefings database.

The module:
  1. Accepts pre-computed workspace metrics and project metric lists.
  2. Builds a structured AI-generated summary (falls back to templated text).
  3. Writes the briefing page with all numeric KPI fields, a prose summary,
     top-priority task list, risk warnings, and project relations.

Founder Briefings DB schema
----------------------------
Briefing Title   title
Date             date
Open Tasks       number
High Priority Tasks number
Overdue Tasks    number
Projects At Risk number
Summary          text
Top Priorities   text
Linked Projects  relation → Projects DB
"""

from __future__ import annotations

import time
import re
from datetime import date

from config import (
    notion,
    FOUNDER_BRIEFINGS_DATABASE_ID,
    TASKS_DATA_SOURCE,
    openai_client,
    gemini_client,
    GEMINI_API_KEY,
    OPENAI_TIMEOUT_SEC,
)
from analytics_engine import ProjectMetrics

_BRIEFING_PROMPT_TEMPLATE = """
You are the AI Chief Operating Officer of a startup. Write a concise executive
summary (3-5 sentences) for the founder's daily briefing based on the metrics
below. Be direct and insightful - highlight risks and strong progress alike.

Metrics:
  Open tasks:          {open_tasks}
  High-priority tasks: {high_priority}
  Overdue tasks:       {overdue}
  Active projects:     {project_count}

Project breakdown:
{project_lines}

Risk warnings:
{risk_lines}

Return ONLY the summary paragraph. No headers, no bullet points, no markdown.
""".strip()


def _build_prompt(
    workspace_counts: dict,
    all_metrics: list[ProjectMetrics],
) -> str:
    project_lines = "\n".join(
        f"  • {m['project_name']}: {m['completed_tasks']}/{m['total_tasks']} tasks "
        f"({m['progress_pct']}%) - Risk: {m['risk_level']}"
        for m in all_metrics
    ) or "  No projects found."

    risk_lines = "\n".join(
        f" {m['project_name']}: {'; '.join(m['risk_reasons'])}"
        for m in all_metrics
        if m["risk_level"] in ("High", "Medium") and m["risk_reasons"]
    ) or "  No significant risks detected."

    return _BRIEFING_PROMPT_TEMPLATE.format(
        open_tasks     = workspace_counts.get("open", 0),
        high_priority  = workspace_counts.get("high_priority", 0),
        overdue        = workspace_counts.get("overdue", 0),
        project_count  = len(all_metrics),
        project_lines  = project_lines,
        risk_lines     = risk_lines,
    )


def _ai_summary_openai(prompt: str) -> str:
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FTE
    def _call():
        resp = openai_client.chat.completions.create(
            model    = "gpt-4o-mini",
            messages = [{"role": "user", "content": prompt}],
            temperature = 0.4,
        )
        return resp.choices[0].message.content.strip()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(_call).result(timeout=OPENAI_TIMEOUT_SEC)
    except FTE:
        raise RuntimeError("OpenAI timed out")


def _ai_summary_gemini(prompt: str) -> str:
    from google.genai.errors import ClientError as GeminiClientError
    def _do():
        resp = gemini_client.models.generate_content(
            model    = "gemini-2.5-flash-lite",
            contents = prompt,
        )
        return resp.text.strip()
    try:
        return _do()
    except GeminiClientError as exc:
        if "429" not in str(exc):
            raise
        wait = 30
        m = re.search(r"retry in ([\d.]+)s", str(exc), re.IGNORECASE)
        if m:
            wait = float(m.group(1)) + 2
        print(f"  Gemini rate-limited - waiting {wait:.0f}s …")
        time.sleep(wait)
        return _do()


def _template_summary(
    workspace_counts: dict,
    all_metrics: list[ProjectMetrics],
) -> str:
    """Rule-based fallback when no AI is available."""
    open_t = workspace_counts.get("open", 0)
    hp     = workspace_counts.get("high_priority", 0)
    ov     = workspace_counts.get("overdue", 0)
    n_proj = len(all_metrics)

    at_risk = [m for m in all_metrics if m["risk_level"] in ("High", "Medium")]
    strong  = [m for m in all_metrics if m["progress_pct"] >= 60]

    summary = (
        f"There are {open_t} open task(s) across {n_proj} project(s). "
        f"{hp} high-priority task(s) remain unresolved and {ov} task(s) are overdue. "
    )
    if strong:
        names = ", ".join(m["project_name"] for m in strong[:2])
        summary += f"{names} show{'s' if len(strong) == 1 else ''} strong progress. "
    if at_risk:
        names = ", ".join(m["project_name"] for m in at_risk[:2])
        summary += f"Attention may be needed on {names}."
    return summary.strip()


def generate_briefing_summary(
    workspace_counts: dict,
    all_metrics: list[ProjectMetrics],
) -> str:
    """Return an AI-generated (or templated) prose summary string."""
    prompt = _build_prompt(workspace_counts, all_metrics)

    if openai_client:
        try:
            return _ai_summary_openai(prompt)
        except Exception as exc:
            print(f"  OpenAI briefing summary failed ({exc}) - trying Gemini …")

    if GEMINI_API_KEY and gemini_client:
        try:
            return _ai_summary_gemini(prompt)
        except Exception as exc:
            print(f"  Gemini briefing summary failed ({exc}) - using template …")

    return _template_summary(workspace_counts, all_metrics)

def _build_top_priorities_text(all_metrics: list[ProjectMetrics]) -> str:
    """
    Pull the most urgent tasks (high-priority or overdue) from Notion and
    return a plain-text list suitable for the Top Priorities property.
    """
    if not TASKS_DATA_SOURCE:
        return "N/A"

    from datetime import date as _date
    today = _date.today()

    try:
        resp = notion.data_sources.query(
            data_source_id = TASKS_DATA_SOURCE,
            filter = {
                "or": [
                    {"property": "Priority", "select":   {"equals": "High"}},
                ]
            },
            page_size = 20,
        )
        pages = resp.get("results", [])
    except Exception:
        return "Could not retrieve top priorities."

    lines: list[str] = []
    for p in pages:
        props = p.get("properties", {})
        status_obj = (props.get("Status") or {}).get("status") or {}
        if status_obj.get("name", "").lower() in ("done", "complete", "completed"):
            continue
        task_title = "".join(
            t.get("plain_text", "")
            for t in (props.get("Task") or {}).get("title", [])
        )
        priority = ((props.get("Priority") or {}).get("select") or {}).get("name", "")
        if task_title:
            lines.append(f"• [{priority}] {task_title}")
        if len(lines) >= 10:
            break

    return "\n".join(lines) if lines else "No urgent open tasks."

def create_founder_briefing(
    workspace_counts: dict,
    all_metrics:      list[ProjectMetrics],
) -> dict:
    """
    Generate a full Founder Daily Briefing and write it to the Founder
    Briefings Notion database.

    Parameters
    ----------
    workspace_counts  Dict with keys: open, high_priority, overdue.
    all_metrics       List of ProjectMetrics from analytics_engine.

    Returns
    -------
    The Notion page dict for the created briefing (empty dict on failure).
    """
    if not FOUNDER_BRIEFINGS_DATABASE_ID:
        print(" FOUNDER_BRIEFINGS_DATABASE_ID not configured - skipping briefing.")
        return {}

    today_iso     = date.today().isoformat()
    briefing_title = f"Founder Briefing - {today_iso}"

    print(f"\nGenerating '{briefing_title}' …")

    summary = generate_briefing_summary(workspace_counts, all_metrics)

    top_priorities = _build_top_priorities_text(all_metrics)

    open_tasks    = workspace_counts.get("open", 0)
    high_priority = workspace_counts.get("high_priority", 0)
    overdue       = workspace_counts.get("overdue", 0)
    at_risk_count = sum(1 for m in all_metrics if m["risk_level"] in ("High", "Medium"))

    project_ids = [m["project_id"] for m in all_metrics]

    risk_warnings = [
        f"⚠ {m['project_name']}: {'; '.join(m['risk_reasons'])}"
        for m in all_metrics
        if m["risk_level"] in ("High", "Medium") and m["risk_reasons"]
    ]
    if risk_warnings:
        summary += "\n\nProject Risk Detected:\n" + "\n".join(risk_warnings)

    properties: dict = {
        "Briefing Title": {
            "title": [{"text": {"content": briefing_title}}]
        },
        "Date": {
            "date": {"start": today_iso}
        },
        "Open Tasks":          {"number": open_tasks},
        "High Priority Tasks": {"number": high_priority},
        "Overdue Tasks":       {"number": overdue},
        "Projects At Risk":    {"number": at_risk_count},
        "Summary": {
            "rich_text": [{"text": {"content": summary[:2000]}}]
        },
        "Top Priorities": {
            "rich_text": [{"text": {"content": top_priorities[:2000]}}]
        },
    }

    if project_ids:
        properties["Linked Projects"] = {
            "relation": [{"id": pid} for pid in project_ids]
        }

    try:
        page = notion.pages.create(
            parent     = {"database_id": FOUNDER_BRIEFINGS_DATABASE_ID},
            properties = properties,
        )
        print(f"  ✔ Briefing created: {page.get('url', '')}")
        return page
    except Exception as exc:
        print(f" Could not create Founder Briefing: {exc}")
        return {}
