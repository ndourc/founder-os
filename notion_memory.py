"""
Notion Memory - Feature 3
==========================
Persists strategic insights extracted from meetings into the
Founder Memory database.  Each entry records the insight title and summary,
a category, a confidence score (1-5), and optional relations back to the
source Meeting and related Project.

Founder Memory DB schema (key properties)
------------------------------------------
Insight        title
Category       select  - Strategy | Product | Growth | Operations | Hiring | Finance
Confidence     number  - 1 (low) … 5 (high)
Created At     date
Source Meeting relation -> Meetings DB
Related Project relation -> Projects DB
"""

from __future__ import annotations

from datetime import date

from config import notion, FOUNDER_MEMORY_DATABASE_ID

VALID_CATEGORIES = {
    "Strategy", "Product", "Growth",
    "Operations", "Hiring", "Finance",
}


def _normalise_category(raw: str) -> str:
    """Map an arbitrary LLM string to one of the valid Notion select options."""
    raw = raw.strip().title()
    if raw in VALID_CATEGORIES:
        return raw
    lower = raw.lower()
    if "product" in lower:
        return "Product"
    if "hir" in lower or "talent" in lower or "recruit" in lower:
        return "Hiring"
    if "growth" in lower or "market" in lower or "customer" in lower:
        return "Growth"
    if "financ" in lower or "revenue" in lower or "cost" in lower:
        return "Finance"
    if "operat" in lower or "process" in lower or "infra" in lower:
        return "Operations"
    return "Strategy"


def _clamp_confidence(value) -> int:
    """Ensure confidence is an integer in the range 1-5."""
    try:
        return max(1, min(5, int(value)))
    except (TypeError, ValueError):
        return 3


def create_memory_entry(
    insight_title: str,
    insight_summary: str,
    category: str        = "Strategy",
    confidence: int      = 3,
    meeting_page_id: str | None = None,
    project_page_id: str | None = None,
) -> dict:
    """
    Create one entry in the Founder Memory Notion database.

    Parameters
    ----------
    insight_title    Short, punchy title for the insight.
    insight_summary  1-2 sentence summary of the insight / decision.
    category         One of: Strategy, Product, Growth, Operations, Hiring, Finance.
    confidence       Confidence score 1-5 (default 3 = medium).
    meeting_page_id  Optional Notion page ID of the source meeting.
    project_page_id  Optional Notion page ID of the related project.

    Returns
    -------
    The full Notion page dict for the newly created entry.
    """
    if not FOUNDER_MEMORY_DATABASE_ID:
        print("FOUNDER_MEMORY_DATABASE_ID not configured - skipping memory entry.")
        return {}

    properties: dict = {
        "Insight": {
            "title": [{"text": {"content": insight_title[:255]}}]
        },
        "Category": {
            "select": {"name": _normalise_category(category)}
        },
        "Confidence": {
            "number": _clamp_confidence(confidence)
        },
        "Created At": {
            "date": {"start": date.today().isoformat()}
        },
    }

    if meeting_page_id:
        properties["Source Meeting"] = {
            "relation": [{"id": meeting_page_id}]
        }

    if project_page_id:
        properties["Related Project"] = {
            "relation": [{"id": project_page_id}]
        }

    page = notion.pages.create(
        parent     = {"database_id": FOUNDER_MEMORY_DATABASE_ID},
        properties = properties,
        children   = [
            {
                "object": "block",
                "type":   "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": insight_summary[:2000]}}
                    ]
                },
            }
        ],
    )
    return page


def store_insights_from_meeting(
    insights: list[dict],
    meeting_page_id: str | None = None,
    project_page_id: str | None = None,
) -> int:
    """
    Iterate a list of insight dicts (from the LLM extractor) and persist each
    one to Notion.

    Expected insight dict schema
    ----------------------------
    {
      "title":      "We are pivoting to enterprise",
      "summary":    "The team agreed to focus on B2B after customer feedback.",
      "category":   "Strategy",
      "confidence": 4
    }

    Returns the number of entries successfully created.
    """
    if not insights:
        return 0

    print(f"\n🧠 Storing {len(insights)} strategic insight(s) …")
    created = 0

    for insight in insights:
        title      = insight.get("title", "Untitled Insight")
        summary    = insight.get("summary", "")
        category   = insight.get("category", "Strategy")
        confidence = insight.get("confidence", 3)

        if not title or not summary:
            continue

        try:
            create_memory_entry(
                insight_title   = title,
                insight_summary = summary,
                category        = category,
                confidence      = confidence,
                meeting_page_id = meeting_page_id,
                project_page_id = project_page_id,
            )
            print(f"  ✔ [{category}] {title} (confidence: {_clamp_confidence(confidence)}/5)")
            created += 1
        except Exception as exc:
            print(f"Could not store insight '{title}': {exc}")

    return created
