from config import notion, PROJECTS_DATABASE_ID

def get_or_create_project(project_name: str) -> str:
    """Finds an existing project by name, or creates a new one. Returns the project page ID."""
    print(f"Checking for project '{project_name}' …")
    
    db = notion.databases.retrieve(database_id=PROJECTS_DATABASE_ID)
    ds_id = db['data_sources'][0]['id']
    ds = notion.data_sources.retrieve(data_source_id=ds_id)
    
    title_prop_name = "Project Name"
    for k, v in ds.get("properties", {}).items():
        if v.get("type") == "title":
            title_prop_name = k
            break

    response = notion.data_sources.query(
        data_source_id=ds_id,
        filter={
            "property": title_prop_name,
            "title": {
                "equals": project_name
            }
        }
    )
    
    results = response.get("results", [])
    if results:
        print(f"  ✔ Found existing project.")
        return results[0]["id"]
        
    print(f"  + Creating new project: {project_name}")
    new_page = notion.pages.create(
        parent={"database_id": PROJECTS_DATABASE_ID},
        properties={
            title_prop_name: {
                "title": [{"text": {"content": project_name}}]
            }
        }
    )
    return new_page["id"]

def update_project_relations(project_id: str, meeting_id: str, task_ids: list):
    """Update the Project page to include the Meeting and Tasks relations."""
    print(f"Linking Meeting and {len(task_ids)} Task(s) to Project …")
    
    if meeting_id:
        try:
            page = notion.pages.retrieve(page_id=project_id)
            current_meetings = page.get("properties", {}).get("Meetings", {}).get("relation", [])
            current_tasks = page.get("properties", {}).get("Tasks", {}).get("relation", [])
            
            meetings_relation = current_meetings + [{"id": meeting_id}]
            tasks_relation = current_tasks + [{"id": tid} for tid in task_ids]
            
            notion.pages.update(
                page_id=project_id,
                properties={
                    "Meetings": {"relation": meetings_relation},
                    "Tasks": {"relation": tasks_relation}
                }
            )
            print("  ✔ Successfully linked to Project.")
        except Exception as e:
            print(f"Could not update Project relations (is the relation name correct?): {e}")
