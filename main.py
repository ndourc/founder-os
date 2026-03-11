"""
Founder OS - Meeting Notes -> Notion Tasks Pipeline
====================================================
Flow:
  meeting_notes  ->  AI extracts tasks  ->  notion-create-pages  ->  Tasks DB
"""

import sys
from llm_extractor import extract_meeting_and_tasks
from notion_projects import get_or_create_project, update_project_relations
from notion_meetings import create_notion_meeting
from notion_tasks import create_notion_task


def push_meeting_and_tasks_to_notion(meeting_data: dict, full_notes: str) -> None:
    """Create meeting and loop over extracted tasks to insert and link them."""
    
    project_id = None
    project_name = meeting_data.get("project_name")
    if project_name and project_name.lower() != "none" and project_name.lower() != "general project":
        project_id = get_or_create_project(project_name)

    meeting_page = create_notion_meeting(meeting_data, full_notes)
    meeting_id = meeting_page.get("id")
    meeting_url = meeting_page.get("url")
    print(f"  ✔ Meeting Created: {meeting_data.get('title')}")
    print(f"    {meeting_url}\n")
    
    tasks = meeting_data.get("tasks", [])
    task_ids = []
    if tasks:
        print("Pushing linked tasks to Notion …\n")
        created_urls = []

        for task in tasks:
            title    = task.get("title", "Untitled task")
            priority = task.get("priority", "Medium")

            page = create_notion_task(title, priority, meeting_page_id=meeting_id)
            tid  = page.get("id")
            url  = page.get("url", "")
            task_ids.append(tid)
            created_urls.append((title, url))
            print(f"  ✔  [{priority}]  {title}")
            print(f"       {url}\n")

        print(f"─────────────────────────────────────────────")
        print(f"{len(created_urls)} task(s) added and linked to Meeting.")
    else:
        print("No tasks to push.")

    if project_id:
        update_project_relations(project_id, meeting_id, task_ids)

EXAMPLE_NOTES = """
Meeting - Product Sprint Kick-off  |  March 10, 2026

Project: Project Hyperion
Attendees: Alice (PM), Bob (Eng), Carol (Design)

Notes:
- We need to ship the landing page by end of week. Alice owns this.
- Bob will create an analytics dashboard to track sign-ups.
- There is a critical login bug reported by three beta users - Bob to fix ASAP.
- Carol to design new onboarding screens for v2.
- Schedule a user-interview session for next Thursday.
"""

def main():
    if len(sys.argv) > 1:
        notes_path = sys.argv[1]
        with open(notes_path, "r", encoding="utf-8") as f:
            meeting_notes = f.read()
        print(f"Reading notes from: {notes_path}\n")
    elif not sys.stdin.isatty():
        meeting_notes = sys.stdin.read()
        print("Reading notes from stdin …\n")
    else:
        print("ℹ No input provided - running with built-in demo notes.\n")
        print("─" * 60)
        print(EXAMPLE_NOTES.strip())
        print("─" * 60 + "\n")
        meeting_notes = EXAMPLE_NOTES

    result = extract_meeting_and_tasks(meeting_notes)
    if result:
        push_meeting_and_tasks_to_notion(result, meeting_notes)


if __name__ == "__main__":
    main()
