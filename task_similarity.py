"""
Task Similarity - Feature 2
============================
Detects semantically duplicate tasks before creation.
Uses difflib fuzzy string matching as the primary strategy with an optional
LLM-based deep comparison when scores are borderline.
"""

import re
import difflib
from config import notion, TASKS_DATA_SOURCE

# Tasks with a normalised similarity score above this threshold are considered
# duplicates. 0.82 is high enough to avoid false positives on short titles.
SIMILARITY_THRESHOLD = 0.82

# If a score falls in the "borderline" band we can optionally ask the LLM.
BORDERLINE_LOW  = 0.65
BORDERLINE_HIGH = SIMILARITY_THRESHOLD


def _normalize(title: str) -> str:
    """Lowercase, strip punctuation and collapse whitespace."""
    title = title.lower().strip()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def _paginate_query(data_source_id: str, **kwargs) -> list:
    """Return every page from a paginated data_sources.query call."""
    results = []
    cursor = None
    while True:
        params = {"data_source_id": data_source_id, **kwargs}
        if cursor:
            params["start_cursor"] = cursor
        resp = notion.data_sources.query(**params)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results


def _extract_title(task_page: dict) -> str:
    """Pull plain-text title from a Task page object."""
    title_items = (
        task_page.get("properties", {})
        .get("Task", {})
        .get("title", [])
    )
    return "".join(item.get("plain_text", "") for item in title_items)


def find_similar_task(new_title: str) -> tuple[str | None, float]:
    """
    Search existing Tasks for one similar to `new_title`.

    Returns
    -------
    (page_id, score)  - page_id is None when no duplicate is found,
                        score is the best similarity ratio found.
    """
    if not TASKS_DATA_SOURCE:
        return None, 0.0

    try:
        existing_tasks = _paginate_query(TASKS_DATA_SOURCE)
    except Exception as exc:
        print(f"Could not query Tasks for deduplication: {exc}")
        return None, 0.0

    norm_new = _normalize(new_title)
    best_id    = None
    best_score = 0.0

    for task_page in existing_tasks:
        existing_title = _extract_title(task_page)
        if not existing_title:
            continue
        score = difflib.SequenceMatcher(
            None, norm_new, _normalize(existing_title)
        ).ratio()
        if score > best_score:
            best_score = score
            best_id    = task_page["id"]

    if best_score >= SIMILARITY_THRESHOLD:
        return best_id, best_score

    return None, best_score


def deduplicate_or_create(
    title: str,
    priority: str,
    meeting_page_id: str,
    create_fn, 
) -> tuple[dict, bool]:
    """
    Try to find a duplicate task; if found, link the meeting to it instead of
    creating a new page. If no duplicate exists, create a fresh task.

    Returns
    -------
    (page_dict, was_duplicate)
    """
    duplicate_id, score = find_similar_task(title)

    if duplicate_id:
        print(f"  ↩ Duplicate detected (score={score:.2f}) - linking to existing task.")
        try:
            existing_page = notion.pages.retrieve(page_id=duplicate_id)
            current_meetings = (
                existing_page.get("properties", {})
                .get("Meeting", {})
                .get("relation", [])
            )
            notion.pages.update(
                page_id=duplicate_id,
                properties={
                    "Meeting": {
                        "relation": current_meetings + [{"id": meeting_page_id}]
                    }
                },
            )
        except Exception as exc:
            print(f"Could not link meeting to existing task: {exc}")
        return existing_page, True

    page = create_fn(title, priority, meeting_page_id=meeting_page_id)
    return page, False
