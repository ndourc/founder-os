"""
Analytics Engine - Feature 4 + 5
===================================
Computes project-level operational metrics, detects execution risks, and writes
the results back to the Projects Notion database so the Executive Dashboard
stays current automatically.

Metric mapping
--------------
Total Tasks          -> total pages in the Tasks DB related to this project
Completed Tasks      -> tasks where Status.name == "Done"
Overdue Tasks        -> incomplete tasks where Date.start < today
High Priority Tasks  -> tasks where Priority.select.name == "High" and not Done
Progress Percentage  -> completed / total * 100  (0 when no tasks)
Risk Level           -> select: High / Medium / Low  (see _assess_risk)
"""

from __future__ import annotations

from datetime import date
from typing import TypedDict

from config import (
    notion,
    TASKS_DATA_SOURCE,
    PROJECTS_DATA_SOURCE,
)


class ProjectMetrics(TypedDict):
    project_id:          str
    project_name:        str
    total_tasks:         int
    completed_tasks:     int
    overdue_tasks:       int
    high_priority_tasks: int
    progress_pct:        float
    risk_level:          str
    risk_reasons:        list[str]


_DONE_STATUSES = {"done", "complete", "completed"}


def _paginate_query(data_source_id: str, **kwargs) -> list:
    """Exhaust Notion pagination and return all rows from a data_source query."""
    results: list = []
    cursor = None
    while True:
        params: dict = {"data_source_id": data_source_id, **kwargs}
        if cursor:
            params["start_cursor"] = cursor
        resp = notion.data_sources.query(**params)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results


def _get_prop(page: dict, prop_name: str) -> dict:
    """Safe accessor for a Notion page property dict."""
    return page.get("properties", {}).get(prop_name, {}) or {}


def _status_name(page: dict) -> str:
    prop = _get_prop(page, "Status")
    status_obj = prop.get("status") or {}
    return (status_obj.get("name") or "").lower()


def _priority_name(page: dict) -> str:
    prop = _get_prop(page, "Priority")
    select_obj = prop.get("select") or {}
    return (select_obj.get("name") or "").lower()


def _due_date(page: dict) -> date | None:
    prop = _get_prop(page, "Date")
    date_obj = prop.get("date") or {}
    start = date_obj.get("start")
    if not start:
        return None
    try:
        return date.fromisoformat(start[:10])
    except ValueError:
        return None

def _assess_risk(
    total: int,
    completed: int,
    overdue: int,
    high_priority: int,
    progress_pct: float,
) -> tuple[str, list[str]]:
    """Return (risk_level, list_of_reasons)."""
    reasons: list[str] = []
    score = 0

    if overdue >= 3:
        reasons.append(f"{overdue} overdue tasks")
        score += 3
    elif overdue > 0:
        reasons.append(f"{overdue} overdue task(s)")
        score += 1

    if high_priority >= 3:
        reasons.append(f"{high_priority} unresolved high-priority tasks")
        score += 2
    elif high_priority >= 1:
        score += 1

    if total >= 3 and progress_pct < 20:
        reasons.append(f"Low completion rate ({progress_pct:.0f}%)")
        score += 2

    if total == 0:
        reasons.append("No tasks yet")

    if score >= 4:
        return "High", reasons
    elif score >= 2:
        return "Medium", reasons
    return "Low", reasons

def compute_project_metrics(project_id: str, project_name: str) -> ProjectMetrics:
    """
    Fetch all tasks linked to `project_id` from the Tasks database and compute
    the full set of operational metrics.
    """
    today = date.today()

    tasks = _paginate_query(
        TASKS_DATA_SOURCE,
        filter={
            "property": "Project",
            "relation": {"contains": project_id},
        },
    )

    total          = len(tasks)
    completed      = 0
    overdue        = 0
    high_priority  = 0

    for task_page in tasks:
        status   = _status_name(task_page)
        priority = _priority_name(task_page)
        due      = _due_date(task_page)

        if status in _DONE_STATUSES:
            completed += 1
        else:
            if priority == "high":
                high_priority += 1
            if due and due < today:
                overdue += 1

    progress_pct = round(completed / total * 100, 1) if total > 0 else 0.0
    risk_level, risk_reasons = _assess_risk(
        total, completed, overdue, high_priority, progress_pct
    )

    return ProjectMetrics(
        project_id          = project_id,
        project_name        = project_name,
        total_tasks         = total,
        completed_tasks     = completed,
        overdue_tasks       = overdue,
        high_priority_tasks = high_priority,
        progress_pct        = progress_pct,
        risk_level          = risk_level,
        risk_reasons        = risk_reasons,
    )


def _write_metrics_to_project(project_id: str, metrics: ProjectMetrics) -> None:
    """Write computed metrics back to the Project page as property values."""
    notion.pages.update(
        page_id    = project_id,
        properties = {
            "Total Tasks":         {"number": metrics["total_tasks"]},
            "Completed Tasks":     {"number": metrics["completed_tasks"]},
            "Overdue Tasks":       {"number": metrics["overdue_tasks"]},
            "High Priority Tasks": {"number": metrics["high_priority_tasks"]},
            "Progress Percentage": {"number": metrics["progress_pct"]},
            "Risk Level":          {"select": {"name": metrics["risk_level"]}},
        },
    )


def compute_and_write_all_project_metrics() -> list[ProjectMetrics]:
    """
    Iterate every project in the Projects database, compute its metrics, write
    them back to Notion, and return the full list for downstream use (briefings,
    risk alerts, etc.).
    """
    if not PROJECTS_DATA_SOURCE:
        print(" PROJECTS_DATA_SOURCE not configured - skipping analytics.")
        return []

    print("\nComputing project analytics …")
    projects = _paginate_query(PROJECTS_DATA_SOURCE)

    all_metrics: list[ProjectMetrics] = []

    for project_page in projects:
        project_id = project_page["id"]
        name_items = (
            project_page.get("properties", {})
            .get("Project Name", {})
            .get("title", [])
        )
        project_name = (
            "".join(item.get("plain_text", "") for item in name_items)
            or "Unnamed Project"
        )

        try:
            metrics = compute_project_metrics(project_id, project_name)
            _write_metrics_to_project(project_id, metrics)
            all_metrics.append(metrics)

            indicator = (
                "🔴" if metrics["risk_level"] == "High"
                else ("🟠" if metrics["risk_level"] == "Medium" else "🟢")
            )
            print(
                f"  {indicator} {project_name}: "
                f"{metrics['completed_tasks']}/{metrics['total_tasks']} tasks "
                f"({metrics['progress_pct']}%)  Risk: {metrics['risk_level']}"
            )
        except Exception as exc:
            print(f" Could not compute metrics for '{project_name}': {exc}")

    print(f"  ✔ Updated {len(all_metrics)} project(s).\n")
    return all_metrics


def get_workspace_task_counts() -> dict:
    """
    Return aggregate counts across ALL tasks (not per-project).
    Used by the Founder Daily Briefing.
    """
    if not TASKS_DATA_SOURCE:
        return {"open": 0, "high_priority": 0, "overdue": 0}

    today = date.today()
    all_tasks = _paginate_query(TASKS_DATA_SOURCE)

    open_tasks      = 0
    high_priority   = 0
    overdue         = 0

    for task_page in all_tasks:
        status   = _status_name(task_page)
        priority = _priority_name(task_page)
        due      = _due_date(task_page)

        if status not in _DONE_STATUSES:
            open_tasks += 1
            if priority == "high":
                high_priority += 1
            if due and due < today:
                overdue += 1

    return {
        "open":          open_tasks,
        "high_priority": high_priority,
        "overdue":       overdue,
    }
