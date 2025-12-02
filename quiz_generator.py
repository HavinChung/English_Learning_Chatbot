import json
from client import call_llm

SYSTEM_PROMPT_PERSONALIZED_QUIZ = """
Generate 5 English quiz questions.

Difficulty: A=advanced, B=upper-intermediate, C=intermediate, D=beginner
Use student's weaknesses (vocab/grammar) from profile.

Output JSON only (no markdown):
[
  {
    "question": "...",
    "choices": ["...", "...", "...", "..."],
    "answer_index": 0,
    "explanation": "Why correct (1 sentence)"
  }
]
"""


def extract_json_list(text: str) -> str:
    start_idx = text.find("[")
    end_idx = text.rfind("]")
    
    if start_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    return text


def generate_personalized_quiz(summary: dict):
    summary_text = json.dumps(summary, ensure_ascii=False)
    prompt = f"Student summary:\n{summary_text}"
    
    try:
        raw_response = call_llm(SYSTEM_PROMPT_PERSONALIZED_QUIZ, prompt)
        json_array = extract_json_list(raw_response)
        questions = json.loads(json_array)
    except Exception:
        return []

    # Validate and clean questions
    valid_questions = []
    for q in questions:
        is_valid = (
            isinstance(q, dict) and
            isinstance(q.get("question"), str) and
            isinstance(q.get("choices"), list) and
            len(q["choices"]) == 4 and
            isinstance(q.get("answer_index"), int) and
            0 <= q["answer_index"] < 4
        )
        
        if is_valid:
            if "explanation" not in q:
                q["explanation"] = ""
            valid_questions.append(q)

    return valid_questions[:5]
