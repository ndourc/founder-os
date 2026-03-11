from config import notion, TASKS_DATABASE_ID

def create_notion_task(title: str, priority: str = "Medium", meeting_page_id: str = None) -> dict:
    """Create a single task page in the Notion Tasks database, linked to a Meeting."""
    properties = {
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
        
    page = notion.pages.create(
        parent={"database_id": TASKS_DATABASE_ID},
        properties=properties
    )
    return page
