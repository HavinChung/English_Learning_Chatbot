import re
from vocab_store import VocabStore
from client import call_llm

store = VocabStore("data/vocab_data.json")


def extract_vocab_target(user_input: str):
    text = user_input.strip()
    lower = text.lower()

    quoted = re.search(r'["\'](.+?)["\']', text)
    if quoted:
        return quoted.group(1).strip()

    patterns = [
        r"what does\s+(.+?)\s+mean",
        r"what is the meaning of\s+(.+?)(?:\?|$)",
        r"what's the meaning of\s+(.+?)(?:\?|$)",
        r"what is the definition of\s+(.+?)(?:\?|$)",
        r"definition of\s+(.+?)(?:\?|$)",
        r"meaning of\s+(.+?)(?:\?|$)",
        r"what does the word\s+(.+?)\s+mean",
    ]

    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return match.group(1).strip()

    return None


SYSTEM_PROMPT_VOCAB = """
You are an English vocabulary tutor. Use this exact format:

Word: <target>
Part of Speech: <pos>
Definition: <simple definition in 1-2 sentences>

Examples:
1. <full sentence>
2. <full sentence>

Synonyms: <list or "None">

Rules: No markdown, no phonetics, no translations. Fill all fields.
"""


def find_vocab_entries(target: str):
    key = target.lower()
    entries = store.index_by_word.get(key)
    if entries:
        return entries
    return store.search_substring(key)


def extract_best_entry(entries):
    if not entries:
        return None

    priority = ["noun", "verb", "adjective", "adverb"]
    
    for pos_type in priority:
        for entry in entries:
            pos = (entry.get("part_of_speech") or "").lower()
            if pos == pos_type:
                return entry
    
    return entries[0]


def handle_vocab_core(user_input: str, target: str) -> str:
    entries = find_vocab_entries(target)

    if not entries:
        prompt = f"Target: {target}\n\nDictionary data: NONE"
        return call_llm(SYSTEM_PROMPT_VOCAB, prompt)

    entry = extract_best_entry(entries)
    examples = entry.get("examples", [])
    synonyms = entry.get("synonyms", [])

    prompt = f"""
Target: {target}

Dictionary data:
POS: {entry.get("pos", "N/A")}
Definition: {entry.get("definition", "N/A")}
Example1: {examples[0] if examples else "N/A"}
Example2: {examples[1] if len(examples) > 1 else "N/A"}
Synonyms: {", ".join(synonyms) if synonyms else "None"}
"""

    return call_llm(SYSTEM_PROMPT_VOCAB, prompt)


def handle_vocab(user_input: str) -> str:
    target = extract_vocab_target(user_input)
    if not target:
        return "I couldn't detect which word you're asking about."
    return handle_vocab_core(user_input, target)


def handle_vocab_with_target(user_input: str, target: str) -> str:
    if not target:
        return handle_vocab(user_input)
    return handle_vocab_core(user_input, target)
