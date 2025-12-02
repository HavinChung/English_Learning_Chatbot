import re
from grammar_inference import correct_grammar
from client import call_llm

SYSTEM_PROMPT_GRAMMAR = """
You are a grammar tutor. Follow this EXACT format:

Original: <original sentence>
Corrected: <corrected sentence>

Explanation:
1. Error Type: <1 sentence>
2. Why wrong: <1-2 sentences>
3. Correct Rule: <short rule>

No extra notes/examples.
"""


GRAMMAR_PATTERNS = [
    r"correct the grammar[: ]+(.+)",
    r"correct my sentence[: ]+(.+)",
    r"fix my sentence[: ]+(.+)",
    r"fix the grammar[: ]+(.+)",
    r"check my grammar[: ]+(.+)",
    r"check the grammar[: ]+(.+)",
    r"grammar check[: ]+(.+)",
    r"correct this sentence[: ]+(.+)",
    r"please correct[: ]+(.+)",
    r"please fix[: ]+(.+)",
]


def extract_grammar_target(user_input: str) -> str:
    text = user_input.strip()

    quoted = re.search(r'["\'](.+?)["\']', text)
    if quoted:
        return quoted.group(1).strip()

    for pattern in GRAMMAR_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            sentence = match.group(1).strip()
            if sentence:
                return sentence
    
    return text


def handle_grammar_core(original_sentence: str) -> str:
    corrected = correct_grammar(original_sentence)

    return call_llm(
        SYSTEM_PROMPT_GRAMMAR,
        f"Original: {original_sentence}\nCorrected: {corrected}",
    )


def handle_grammar(user_input: str) -> str:
    original_sentence = extract_grammar_target(user_input)
    return handle_grammar_core(original_sentence)


def handle_grammar_with_target(user_input: str, target_sentence: str) -> str:
    if not target_sentence:
        return handle_grammar(user_input)
    return handle_grammar_core(target_sentence)
