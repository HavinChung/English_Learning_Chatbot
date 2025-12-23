from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from llm_intent import analyze_with_llm
from vocab_handler import handle_vocab, handle_vocab_with_target
from grammar_handler import handle_grammar, handle_grammar_with_target
from client import call_llm
from learning_profile import build_learning_profile, record_quiz_result, record_quiz_session, get_quiz_history
from chat_manager import list_sessions, create_new_session, load_session, append_message, delete_session
from quiz import generate_quiz, generate_explanation

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API request models
class ChatRequest(BaseModel):
    session_id: str
    message: str

class QuizAnswerRequest(BaseModel):
    choice: int

# In-memory quiz state
quiz_sessions = {}

# Format quiz question for display
def format_quiz_question(q: dict, idx: int) -> str:
    lines = [f"Q{idx}: {q['question']}"]
    for i, c in enumerate(q["choices"]):
        lines.append(f"{i+1}. {c}")
    lines.append("")
    lines.append("Please answer with 1, 2, 3, or 4.")
    return "\n".join(lines)



@app.get("/sessions")
def get_sessions():
    return {"sessions": list_sessions()}


@app.delete("/sessions/{session_id}")
def delete_session_endpoint(session_id: str):
    delete_session(session_id)
    return {"ok": True}


@app.post("/sessions/new")
def new_session():
    session_id = create_new_session()
    return {"session_id": session_id}


@app.get("/sessions/{session_id}")
def get_session_data(session_id: str):
    data = load_session(session_id)
    if data is None:
        return {"error": "Session not found"}
    return data


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    session_id = req.session_id
    user_input = req.message.strip()

    session_data = load_session(session_id)
    if session_data is None:
        return {"error": "Invalid session_id"}

    append_message(session_id, "user", user_input)

    analysis = analyze_with_llm(user_input)
    intent = analysis.get("intent", "general_chat")

    vocab_target = analysis.get("vocab_target")
    grammar_target = analysis.get("grammar_target")

    # Route to appropriate handler based on intent
    if intent == "vocab_lookup":
        answer = handle_vocab_with_target(user_input, vocab_target) if vocab_target else handle_vocab(user_input)
    elif intent == "grammar_correction":
        answer = handle_grammar_with_target(user_input, grammar_target) if grammar_target else handle_grammar(user_input)
    else:
        system_prompt_chat = """
English-learning assistant. Be simple and clear.
Only correct/explain grammar when asked.
"""
        answer = call_llm(system_prompt_chat, user_input)

    answer = answer.strip()
    append_message(session_id, "assistant", answer)
    
    # Invalidate profile cache every 5 messages to keep it fresh
    all_sessions = list_sessions()
    total_user_messages = 0
    
    for session_info in all_sessions:
        sid = session_info["session_id"]
        if sid == "quiz_session":
            continue
        session = load_session(sid)
        if session:
            messages = session.get("messages", [])
            total_user_messages += sum(1 for msg in messages if msg.get("role") == "user")
    
    if total_user_messages % 5 == 0:
        from learning_profile import _profile_cache
        _profile_cache["timestamp"] = None
    
    return {"response": answer}


@app.post("/quiz/prepare")
def quiz_prepare():
    profile = build_learning_profile()
    return {"status": "ready", "profile": profile}


@app.post("/quiz/generate")
def quiz_generate(data: dict):
    profile = data.get("profile", data)
    
    # Generate 5 questions from learner profile
    quiz = generate_quiz({"profile": profile}, 5)

    if not quiz:
        return {
            "progress": "-",
            "text": "I couldn't generate a quiz right now. Please try again later."
        }

    # Precompute all explanations
    for q in quiz:
        q["explanation"] = generate_explanation(
            q["original_sentence"], 
            q["correct_answer"], 
            q["topic"]
        )

    quiz_sessions["active"] = {
        "questions": quiz,
        "current": 0,
        "score": 0,
        "answers": []
    }

    first = format_quiz_question(quiz[0], 1)
    return {
        "progress": f"Q1/{len(quiz)}",
        "text": first
    }


@app.post("/quiz/answer")
def quiz_answer(req: QuizAnswerRequest):
    session = quiz_sessions.get("active")
    if not session:
        return {"done": True, "feedback": "Quiz not active"}

    q = session["questions"][session["current"]]
    correct_idx = q["correct_index"]
    is_correct = (req.choice - 1 == correct_idx)

    if is_correct:
        session["score"] += 1
        feedback = "Correct!"
    else:
        correct_choice = f"{correct_idx + 1}. {q['choices'][correct_idx]}"
        feedback = f"Incorrect.\nCorrect answer: {correct_choice}"

    explanation = q["explanation"]

    # Record answer for history
    session["answers"].append({
        "question": q["question"],
        "choices": q["choices"],
        "correct": correct_idx,
        "user_answer": req.choice - 1,
        "is_correct": is_correct,
        "explanation": explanation
    })

    session["current"] += 1

    # Quiz completed - save results
    if session["current"] >= len(session["questions"]):
        record_quiz_session(session["answers"])
        score = session["score"]
        total = len(session["questions"])
        accuracy = (score / total) * 100
        result = record_quiz_result(score, total)

        return {
            "done": True,
            "feedback": feedback,
            "explanation": explanation,
            "final_score": score,
            "total": total,
            "accuracy": accuracy,
            "level": result["level"]
        }

    return {
        "done": False,
        "feedback": feedback,
        "explanation": explanation
    }


@app.get("/quiz/next")
def quiz_next():
    session = quiz_sessions.get("active")
    if not session:
        return {"progress": "-", "text": "No active quiz"}

    q = session["questions"][session["current"]]
    idx = session["current"] + 1

    return {
        "progress": f"Q{idx}/{len(session['questions'])}",
        "text": format_quiz_question(q, idx)
    }


@app.get("/quiz/history")
def get_history():
    return {"history": get_quiz_history()}


@app.post("/profile/invalidate")
def invalidate_profile():
    from learning_profile import _profile_cache
    _profile_cache["timestamp"] = None
    _profile_cache["data"] = None
    return {"status": "invalidated"}
