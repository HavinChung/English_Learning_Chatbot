import os
import json
from datetime import datetime

SESSIONS_DIR = "data/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


def session_path(session_id: str):
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")


def list_sessions():
    sessions = []
    files = sorted(os.listdir(SESSIONS_DIR))

    for filename in files:
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(SESSIONS_DIR, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data["session_id"] == "quiz_session":
                continue

            sessions.append({
                "session_id": data["session_id"],
                "created_at": data["created_at"],
                "title": data.get("title", ""),
            })
        except:
            continue

    return sessions



def create_new_session(session_id: str | None = None):
    if session_id is None:
        files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
        next_id = len(files) + 1
        session_id = f"session_{next_id:03d}"

    data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "title": "",
    }

    path = session_path(session_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return session_id


def load_session(session_id: str):
    filepath = session_path(session_id)
    
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def append_message(session_id: str, role: str, text: str):
    session = load_session(session_id)
    if not session:
        return

    session["messages"].append({"role": role, "text": text})

    if role == "user" and not session.get("title"):
        cleaned_text = text.strip()
        if cleaned_text:
            session["title"] = cleaned_text[:40]

    filepath = session_path(session_id)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)


def delete_session(session_id: str):
    filepath = session_path(session_id)
    
    if not os.path.exists(filepath):
        return False
    
    os.remove(filepath)
    return True
