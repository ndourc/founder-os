import os
from dotenv import load_dotenv
from openai import OpenAI
from google import genai as google_genai
from notion_client import Client

load_dotenv()

NOTION_TOKEN        = os.environ.get("NOTION_TOKEN", "")
OPENAI_API_KEY      = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "")

# Database IDs
TASKS_DATABASE_ID             = os.environ.get("TASKS_DATABASE_ID", "")
MEETINGS_DATABASE_ID          = os.environ.get("MEETINGS_DATABASE_ID", "")
PROJECTS_DATABASE_ID          = os.environ.get("PROJECTS_DATABASE_ID", "")
FOUNDER_MEMORY_DATABASE_ID    = os.environ.get("FOUNDER_MEMORY_DATABASE_ID", "")
FOUNDER_BRIEFINGS_DATABASE_ID = os.environ.get("FOUNDER_BRIEFINGS_DATABASE_ID", "")

# Data Source IDs (for querying via data_sources API)
TASKS_DATA_SOURCE             = os.environ.get("TASKS_DATA_SOURCE", "")
PROJECTS_DATA_SOURCE          = os.environ.get("PROJECTS_DATA_SOURCE", "")
MEETINGS_DATA_SOURCE          = os.environ.get("MEETINGS_DATA_SOURCE", "")
FOUNDER_MEMORY_DATA_SOURCE    = os.environ.get("FOUNDER_MEMORY_DATA_SOURCE", "")
FOUNDER_BRIEFINGS_DATA_SOURCE = os.environ.get("FOUNDER_BRIEFINGS_DATA_SOURCE", "")

OPENAI_TIMEOUT_SEC  = 30

notion        = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
gemini_client = google_genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
