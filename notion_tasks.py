from config import notion, TASKS_DATABASE_ID

def create_notion_task(
    title: str,
    priority: str = "Medium",
    meeting_page_id: str | None = None,
    project_page_id: str | None = None,
) -> dict:
    """Create a single task page in the Notion Tasks database, linked to a Meeting and/or Project."""
    properties: dict = {
        "Task": {
            "title": [{"text": {"content": title}}]
        },
        "Status": {
            "status": {"name": "To do"}
        },
        "Priority": {
            "select": {"name": priority}
        },
    }

    if meeting_page_id:
        properties["Meeting"] = {
            "relation": [{"id": meeting_page_id}]
        }

    if project_page_id:
        properties["Project"] = {
            "relation": [{"id": project_page_id}]
        }

    page = notion.pages.create(
        parent={"database_id": TASKS_DATABASE_ID},
        properties=properties,
    )
    return page
