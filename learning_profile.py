import json
import os
from datetime import datetime, timedelta
from client import call_llm

USER_DATA_FILE = "data/user_data.json"
SESSIONS_DIR = "data/sessions"
os.makedirs("data", exist_ok=True)

_profile_cache = {
    "timestamp": None,
    "data": None
}
CACHE_EXPIRE_MINUTES = 30

SYSTEM_PROMPT_SUMMARIZER = """
You analyze English ability.

Output ONLY this JSON:
{
  "vocab_weakness": [...],
  "grammar_patterns": [...],
  "common_mistakes": [...],
  "overall_skill": "..."
}
If unsure, return empty lists and "N/A".
"""

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Return default data for new user
    return {
        "user_id": "default_user",
        "created_at": datetime.now().isoformat(),
        "profile": {
            "vocab_weakness": [],
            "grammar_patterns": [],
            "common_mistakes": [],
            "overall_skill": "N/A"
        },
        "quiz_history": []
    }

def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_json_object(text: str) -> str:
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    
    if start_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    return "{}"

def load_user_conversations():
    user_messages = []
    
    if not os.path.exists(SESSIONS_DIR):
        return []
    
    session_files = []
    for fname in os.listdir(SESSIONS_DIR):
        if not fname.endswith(".json"):
            continue
        if fname == "quiz_session.json":
            continue
        
        path = os.path.join(SESSIONS_DIR, fname)
        try:
            mtime = os.path.getmtime(path)
            session_files.append((mtime, fname, path))
        except:
            continue
    
    session_files.sort(reverse=True)
    if session_files:
        _, fname, path = session_files[0]
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            messages = session_data.get("messages", [])
            
            for msg in messages:
                if msg.get("role") == "user":
                    user_messages.append(msg.get("text", ""))
        except:
            pass
    
    return user_messages

def summarize_conversations() -> dict:
    user_messages = load_user_conversations()
    
    default = {
        "vocab_weakness": [],
        "grammar_patterns": [],
        "common_mistakes": [],
        "overall_skill": "N/A",
    }
    
    if not user_messages:
        return default

    messages_text = "\n".join(user_messages)
    raw = call_llm(SYSTEM_PROMPT_SUMMARIZER, f"Messages:\n{messages_text}")

    try:
        obj = extract_json_object(raw)
        data = json.loads(obj)
    except:
        data = default

    for k, v in default.items():
        if not isinstance(data.get(k), type(v)):
            data[k] = v

    return data

def calculate_stats(quiz_history: list) -> dict:
    if not quiz_history:
        return {
            "total_quizzes": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "average_accuracy": 0.0,
            "recent_levels": []
        }
    
    total_q = 0
    correct_q = 0
    recent_levels = []
    
    for quiz in quiz_history[-10:]:
        questions = quiz.get("questions", [])
        total_q += len(questions)
        correct_q += sum(1 for q in questions if q.get("is_correct", False))
        
        quiz_correct = sum(1 for q in questions if q.get("is_correct", False))
        quiz_total = len(questions)
        if quiz_total > 0:
            acc = quiz_correct / quiz_total
            if acc >= 0.9: level = "A"
            elif acc >= 0.75: level = "B"
            elif acc >= 0.5: level = "C"
            else: level = "D"
            recent_levels.append(level)
    
    avg_acc = correct_q / total_q if total_q > 0 else 0.0
    
    return {
        "total_quizzes": len(quiz_history),
        "total_questions": total_q,
        "correct_answers": correct_q,
        "average_accuracy": avg_acc,
        "recent_levels": recent_levels[-5:]
    }

def difficulty_from_accuracy(acc: float) -> str:
    if acc >= 0.85: return "A"
    if acc >= 0.7: return "B"
    if acc >= 0.5: return "C"
    return "D"

def build_learning_profile() -> dict:
    if _profile_cache["timestamp"] is not None:
        elapsed = datetime.now() - _profile_cache["timestamp"]
        if elapsed < timedelta(minutes=CACHE_EXPIRE_MINUTES):
            return _profile_cache["data"]

    user_data = load_user_data()
    convo = summarize_conversations()
    stats = calculate_stats(user_data["quiz_history"])
    
    difficulty = difficulty_from_accuracy(stats["average_accuracy"])

    profile = {
        "vocab_weakness": convo["vocab_weakness"],
        "grammar_patterns": convo["grammar_patterns"],
        "common_mistakes": convo["common_mistakes"],
        "overall_skill": convo["overall_skill"],
        "total_quizzes": stats["total_quizzes"],
        "average_accuracy": stats["average_accuracy"],
        "recent_quiz_levels": stats["recent_levels"],
        "quiz_difficulty": difficulty,
    }

    user_data["profile"] = {
        "vocab_weakness": convo["vocab_weakness"],
        "grammar_patterns": convo["grammar_patterns"],
        "common_mistakes": convo["common_mistakes"],
        "overall_skill": convo["overall_skill"]
    }
    save_user_data(user_data)

    _profile_cache["timestamp"] = datetime.now()
    _profile_cache["data"] = profile

    return profile

def record_quiz_session(session_questions: list):
    user_data = load_user_data()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "questions": session_questions
    }
    user_data["quiz_history"].append(entry)
    save_user_data(user_data)

def record_quiz_result(score: int, total: int) -> dict:
    acc = score / total if total > 0 else 0.0
    
    if acc >= 0.9: level = "A"
    elif acc >= 0.75: level = "B"
    elif acc >= 0.5: level = "C"
    else: level = "D"

    _profile_cache["timestamp"] = None
    _profile_cache["data"] = None

    return {
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "total": total,
        "accuracy": acc,
        "level": level,
    }

def get_quiz_history() -> list:
    user_data = load_user_data()
    return user_data["quiz_history"]

def get_user_stats() -> dict:
    user_data = load_user_data()
    return calculate_stats(user_data["quiz_history"])