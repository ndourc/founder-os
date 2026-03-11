import re
from config import notion, MEETINGS_DATABASE_ID

def create_notion_meeting(meeting_data: dict, full_notes: str) -> dict:
    """Create a meeting page in the Meetings database."""
    print("Creating meeting page in Notion …")
    
    properties = {
        "Title of the meeting": {
            "title": [{"text": {"content": meeting_data.get("title", "Untitled Meeting")}}]
        },
        "Full notes": {
            "rich_text": [{"text": {"content": full_notes[:2000]}}]
        },
        "Attendees": {
            "rich_text": [{"text": {"content": meeting_data.get("attendees", "")}}]
        },
    }
    
    date_str = meeting_data.get("date", "")
    if date_str:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            properties["Date"] = {"date": {"start": date_str}}

    page = notion.pages.create(
        parent={"database_id": MEETINGS_DATABASE_ID},
        properties=properties
    )
    return page
