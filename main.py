"""
Founder OS – AI Operational Intelligence Pipeline
===================================================
Full execution flow
-------------------
1.  meeting_notes  →  LLM extraction  →  { title, date, attendees,
                                            project_name, tasks[], insights[] }
2.  Find-or-create the Project page in Notion.
3.  Create the Meeting page in Notion.
4.  For each extracted task:
      a. Run smart duplicate detection (task_similarity).
      b. Create a new task (linking to Meeting + Project) or link the meeting
         to the already-existing duplicate task.
5.  Update the Project page relations (Meetings + Tasks).
6.  Store strategic insights in the Founder Memory database.
7.  Compute per-project and workspace-level analytics; write metrics back to
    the Projects database (Total Tasks, Progress Percentage, Risk Level, …).
8.  Generate and push the Founder Daily Briefing to the Briefings database.
"""

import sys

from llm_extractor        import extract_meeting_and_tasks
from notion_projects      import get_or_create_project, update_project_relations
from notion_meetings      import create_notion_meeting
from notion_tasks         import create_notion_task
from task_similarity      import deduplicate_or_create
from notion_memory        import store_insights_from_meeting
from analytics_engine     import compute_and_write_all_project_metrics, get_workspace_task_counts
from notion_briefings     import create_founder_briefing

def push_meeting_and_tasks_to_notion(meeting_data: dict, full_notes: str) -> None:
    """
    Orchestrate the creation of Meeting, Tasks, and Project pages in Notion,
    then trigger analytics and briefing generation.
    """

    project_id   = None
    project_name = meeting_data.get("project_name") or ""
    if project_name and project_name.lower() not in ("none", "general project", ""):
        project_id = get_or_create_project(project_name)

    meeting_page = create_notion_meeting(meeting_data, full_notes)
    meeting_id   = meeting_page.get("id")
    meeting_url  = meeting_page.get("url")
    print(f"  ✔ Meeting Created: {meeting_data.get('title')}")
    print(f"    {meeting_url}\n")

    tasks    = meeting_data.get("tasks", [])
    task_ids: list[str] = []

    if tasks:
        print("Pushing tasks to Notion …\n")
        for task in tasks:
            title    = task.get("title", "Untitled task")
            priority = task.get("priority", "Medium")

            def _create(t, p, meeting_page_id=None):
                return create_notion_task(
                    t, p,
                    meeting_page_id = meeting_page_id,
                    project_page_id = project_id,
                )

            page, was_duplicate = deduplicate_or_create(
                title          = title,
                priority       = priority,
                meeting_page_id = meeting_id,
                create_fn      = _create,
            )
            tid = page.get("id", "")
            url = page.get("url", "")
            if tid:
                task_ids.append(tid)
            status_label = "↩ Linked existing" if was_duplicate else "✔ Created"
            print(f"  {status_label}  [{priority}]  {title}")
            if url:
                print(f"       {url}\n")

        print(f"─────────────────────────────────────────────")
        duplicates = sum(
            1 for task in tasks
        )
        print(f"{len(task_ids)} task(s) processed.")
    else:
        print("No tasks extracted from these notes.")

    if project_id:
        update_project_relations(project_id, meeting_id, task_ids)

    insights = meeting_data.get("insights", [])
    if insights:
        store_insights_from_meeting(
            insights        = insights,
            meeting_page_id = meeting_id,
            project_page_id = project_id,
        )

    all_metrics = compute_and_write_all_project_metrics()

    workspace_counts = get_workspace_task_counts()
    create_founder_briefing(
        workspace_counts = workspace_counts,
        all_metrics      = all_metrics,
    )


EXAMPLE_NOTES = """
Meeting - Q3 Marketing & Growth Sync  |  April 2, 2026

Project: Project Titan Launch
Attendees: Dave (Marketing), Eve (Sales), Frank (Ops)

Notes:
- Dave must finalize the new LinkedIn ad copy and creative assets by Wednesday.
- Eve to draft the outbound sales email sequence for the new enterprise tier.
- Frank will configure the HubSpot CRM integration and ensure lead routing is working.
- We need to prepare a press release for the Titan launch. Dave owns this.

Decisions:
- We are allocating 60% of our Q3 marketing budget heavily towards LinkedIn direct response campaigns, significantly reducing Facebook spend.
- We decided to pause hiring for a front-end developer and instead prioritize hiring a Sr. Sales Executive to capture the enterprise momentum.
- Operations will switch from weekly to bi-weekly reporting to free up overhead time.
"""


def main() -> None:
    if len(sys.argv) > 1:
        notes_path = sys.argv[1]
        with open(notes_path, "r", encoding="utf-8") as fh:
            meeting_notes = fh.read()
        print(f"Reading notes from: {notes_path}\n")
    elif not sys.stdin.isatty():
        meeting_notes = sys.stdin.read()
        print("Reading notes from stdin …\n")
    else:
        print("No input provided - running with built-in demo notes.\n")
        print("─" * 60)
        print(EXAMPLE_NOTES.strip())
        print("─" * 60 + "\n")
        meeting_notes = EXAMPLE_NOTES

    result = extract_meeting_and_tasks(meeting_notes)
    if result:
        push_meeting_and_tasks_to_notion(result, meeting_notes)


if __name__ == "__main__":
    main()
