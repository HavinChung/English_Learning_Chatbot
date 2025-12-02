import json
from client import call_llm_fast


SYSTEM_PROMPT_INTENT = """"
Intent analyzer for English-learning chatbot.

Intents:
- "vocab_lookup": asking word/phrase meaning
- "grammar_correction": asking sentence correction
- "general_chat": anything else

Extract targets:
- vocab_lookup: extract word/phrase → vocab_target
- grammar_correction: extract sentence → grammar_target
- general_chat: both null
- Prefer quoted text ("..." or '...')

Output JSON only (no markdown/backticks):
{
  "intent": "vocab_lookup" | "grammar_correction" | "general_chat",
  "vocab_target": string | null,
  "grammar_target": string | null
}
"""

def extract_json_block(text: str) -> str:
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    
    if start_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
    
    return text


def analyze_with_llm(user_input: str) -> dict:
    default_response = {
        "intent": "general_chat",
        "vocab_target": None,
        "grammar_target": None,
    }

    try:
        raw_response = call_llm_fast(SYSTEM_PROMPT_INTENT, user_input)
        json_text = extract_json_block(raw_response)
        data = json.loads(json_text)
    except Exception:
        return default_response

    # Validate and extract fields
    intent = data.get("intent", "general_chat")
    if not isinstance(intent, str):
        intent = "general_chat"

    vocab_target = data.get("vocab_target")
    if vocab_target and not isinstance(vocab_target, str):
        vocab_target = None

    grammar_target = data.get("grammar_target")
    if grammar_target and not isinstance(grammar_target, str):
        grammar_target = None

    return {
        "intent": intent,
        "vocab_target": vocab_target,
        "grammar_target": grammar_target,
    }
