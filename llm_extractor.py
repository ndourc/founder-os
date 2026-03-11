import json
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from config import openai_client, gemini_client, OPENAI_TIMEOUT_SEC, GEMINI_API_KEY

EXTRACTION_PROMPT = """
You are an expert at reading meeting notes. Extract the meeting details, actionable tasks, and the main project discussed.

Return ONLY a valid JSON object matching this structure EXACTLY:
{
  "title": "Short descriptive meeting title",
  "date": "YYYY-MM-DD",
  "attendees": "Comma separated list of names",
  "project_name": "Name of the overarching project (if any)",
  "tasks": [
    {"title": "Task title", "priority": "High/Medium/Low"}
  ]
}

If no date is specified, use today's date or omit the date.
Do NOT include any markdown, explanation, or extra text - only the JSON object.
"""

def _parse_json_meeting(raw: str) -> dict:
    """Parse a JSON object from a model response, stripping code fences."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse valid JSON from model response:\n{raw}")

def _call_openai(meeting_notes: str) -> dict:
    """Call OpenAI synchronously (run inside a thread for timeout control)."""
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user",   "content": meeting_notes},
        ],
        temperature=0.2,
    )
    return _parse_json_meeting(response.choices[0].message.content.strip())

def _call_gemini(meeting_notes: str) -> dict:
    """Call Gemini as a fallback. Handles 429 by waiting the suggested retry
    delay (extracted from the error message) and retrying once."""
    from google.genai.errors import ClientError as GeminiClientError

    prompt = EXTRACTION_PROMPT.strip() + "\n\nMeeting notes:\n" + meeting_notes

    def _do_call() -> dict:
        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt,
        )
        return _parse_json_meeting(response.text.strip())

    try:
        return _do_call()
    except GeminiClientError as exc:
        if "429" not in str(exc) and exc.status != "RESOURCE_EXHAUSTED":
            raise
        wait_sec = 30 
        match = re.search(r"retry in ([\d.]+)s", str(exc), re.IGNORECASE)
        if match:
            wait_sec = float(match.group(1)) + 2
        print(f"Gemini rate-limited (429) - waiting {wait_sec:.0f}s then retrying …")
        time.sleep(wait_sec)
        return _do_call()

def _call_rule_based(meeting_notes: str) -> dict:
    """Fallback rule-based extraction for when AI is completely unavailable."""
    title = "Untitled Meeting"
    date_str = datetime.now().strftime("%Y-%m-%d")
    attendees = ""
    tasks = []

    lines = meeting_notes.splitlines()
    for line in lines:
        lower_line = line.lower()
        if "meeting -" in line or "meeting:" in lower_line:
            title = line.split("|")[0].replace("Meeting -", "").replace("Meeting:", "").strip()
        if "attendees:" in lower_line:
            attendees = line[line.lower().find("attendees:") + 10:].strip()
        
        if line.strip().startswith("-") or line.strip().startswith("*"):
            if "to " in lower_line or "will " in lower_line:
                tasks.append({
                    "title": line.strip("-* ").strip(),
                    "priority": "Medium"
                })

    return {
        "title": title or "Untitled Meeting",
        "date": date_str,
        "attendees": attendees,
        "project_name": "General Project",
        "tasks": tasks
    }

def extract_meeting_and_tasks(meeting_notes: str) -> dict:
    """Extract meeting details and tasks using OpenAI -> Gemini -> Rule-based fallback."""
    print("Extracting details from meeting notes …")

    result = None

    if openai_client:
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_call_openai, meeting_notes)
                result = future.result(timeout=OPENAI_TIMEOUT_SEC)
            print("provider: OpenAI ✔")
        except FuturesTimeoutError:
            print(f"OpenAI did not respond within {OPENAI_TIMEOUT_SEC}s - switching to Gemini …")
        except Exception as exc:
            print(f"OpenAI error ({exc}) - switching to Gemini …")
    else:
        print(" No OpenAI key configured - using Gemini directly …")

    if result is None:
        if GEMINI_API_KEY:
            try:
                result = _call_gemini(meeting_notes)
                print("provider: Gemini ✔")
            except Exception as exc:
                print(f"Gemini error ({exc}) - switching to rule-based fallback …")
                result = _call_rule_based(meeting_notes)
                print("provider: Rule-based ✔")
        else:
            print(" No Gemini key configured - using rule-based fallback …")
            result = _call_rule_based(meeting_notes)
            print("provider: Rule-based ✔")

    print(f"Extracted Meeting: {result.get('title')}")
    print(f"Extracted {len(result.get('tasks', []))} task(s)\n")
    return result
