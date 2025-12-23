import json
import random
import difflib
from transformers import T5Tokenizer, T5ForConditionalGeneration
from client import call_llm

USER_DATA_PATH = "data/user_data.json"
NUM_QUESTIONS = 5

# Load fine-tuned T5 model for fill-in-the-blank generation
tokenizer = T5Tokenizer.from_pretrained("models/checkpoint-91593")
model = T5ForConditionalGeneration.from_pretrained("models/checkpoint-91593")

# Word pools for each grammar category
TOPICS = {
    "article": ["a", "an", "the"],
    "sva": ["is", "are", "was", "were", "has", "have"],
    "tense": ["go", "goes", "went", "gone"],
    "preposition": ["in", "on", "at", "to", "for", "from"],
    "comparative": ["more", "less", "better", "worse"],
    "wh": ["who", "what", "where", "when", "why", "how"]
}

# Sentence templates by topic and difficulty level
SKELETONS = {
    "article": {
        "Basic": [
            "I bought <extra_id_0> apple.",
            "She saw <extra_id_0> elephant.",
            "He needs <extra_id_0> umbrella."
        ],
        "Intermediate": [
            "I bought <extra_id_0> interesting book yesterday.",
            "She found <extra_id_0> old painting in the attic.",
            "They visited <extra_id_0> historical site during their trip."
        ],
        "Advanced": [
            "After hours of searching, she finally discovered <extra_id_0> unique artifact hidden beneath the ruins.",
            "He adopted <extra_id_0> abandoned dog that had been wandering around the neighborhood.",
            "Researchers published <extra_id_0> article detailing the results of the experiment."
        ]
    },
    "sva": {
        "Basic": [
            "The students <extra_id_0> late.",
            "My friends <extra_id_0> here.",
            "The dog <extra_id_0> loud."
        ],
        "Intermediate": [
            "The students <extra_id_0> always late for class.",
            "My friends <extra_id_0> going to the festival this weekend.",
            "The dogs <extra_id_0> barking loudly every night."
        ],
        "Advanced": [
            "The committee <extra_id_0> deciding whether to approve the new policy.",
            "The data <extra_id_0> showing a significant improvement in performance.",
            "Neither the teacher nor the students <extra_id_0> aware of the schedule change."
        ]
    },
    "tense": {
        "Basic": [
            "Tom <extra_id_0> to school yesterday.",
            "She <extra_id_0> lunch.",
            "I <extra_id_0> a movie."
        ],
        "Intermediate": [
            "She <extra_id_0> the report before the deadline.",
            "They <extra_id_0> dinner when I arrived.",
            "I <extra_id_0> this movie last weekend."
        ],
        "Advanced": [
            "By the time I arrived, they <extra_id_0> the entire presentation.",
            "She <extra_id_0> working on the project for several hours before taking a break.",
            "He <extra_id_0> to understand the concept after reviewing the notes."
        ]
    },
    "preposition": {
        "Basic": [
            "She arrived <extra_id_0> the airport.",
            "He sat <extra_id_0> the chair.",
            "The keys are <extra_id_0> the table."
        ],
        "Intermediate": [
            "We will meet <extra_id_0> 7 PM.",
            "He works <extra_id_0> a tech company.",
            "The picture is <extra_id_0> the wall."
        ],
        "Advanced": [
            "She succeeded <extra_id_0> completing the task despite the difficulties.",
            "He insisted <extra_id_0> joining the meeting even though he was sick.",
            "They participated <extra_id_0> the event held downtown."
        ]
    },
    "comparative": {
        "Basic": [
            "This laptop is <extra_id_0> powerful.",
            "She is <extra_id_0> tall.",
            "My score is <extra_id_0> good."
        ],
        "Intermediate": [
            "This laptop is <extra_id_0> powerful than that one.",
            "She is <extra_id_0> skilled than John.",
            "The new phone is <extra_id_0> expensive than the old one."
        ],
        "Advanced": [
            "His explanation was <extra_id_0> clear than the previous one despite the complexity.",
            "The revised design is <extra_id_0> efficient compared with earlier models.",
            "Her performance was <extra_id_0> impressive considering the limited time."
        ]
    },
    "wh": {
        "Basic": [
            "<extra_id_0> is your name?",
            "<extra_id_0> are you?",
            "<extra_id_0> is he?"
        ],
        "Intermediate": [
            "<extra_id_0> is your favorite subject?",
            "<extra_id_0> did you meet yesterday?",
            "<extra_id_0> do you usually wake up?"
        ],
        "Advanced": [
            "<extra_id_0> factors influenced the outcome of the experiment?",
            "<extra_id_0> reason did she give for rejecting the proposal?",
            "<extra_id_0> circumstances led to the unexpected result?"
        ]
    }
}

def load_user(path):
    with open(path) as f:
        return json.load(f)

# Extract weak grammar topics from learner profile
def detect_topics(profile):
    topics = list(set(profile.get("grammar_patterns", []) + profile.get("common_mistakes", [])))
    allowed = set(TOPICS.keys())
    topics = [t for t in topics if t in allowed]
    if not topics:
        topics = ["article", "sva"]
    return topics

# Weighted random selection: 60% weak topics, 40% others
def select_topic(profile):
    weak = detect_topics(profile)
    all_topics = list(TOPICS.keys())
    w = {}
    for t in all_topics:
        if t in weak:
            w[t] = 0.6 / len(weak)
        else:
            w[t] = 0.4 / (len(all_topics) - len(weak))
    keys = list(w.keys())
    weights = list(w.values())
    return random.choices(keys, weights=weights, k=1)[0]

# Generate completed sentence from skeleton with <extra_id_0>
def fill_blank(sentence):
    enc = tokenizer(sentence, return_tensors="pt")
    out = model.generate(**enc, max_new_tokens=32)
    return tokenizer.decode(out[0], skip_special_tokens=True)

# Find the word that filled the blank position
def extract_answer(skeleton, corrected):
    sk_tokens = skeleton.split()
    cor_tokens = corrected.split()
    if "<extra_id_0>" not in sk_tokens:
        return None, corrected
    blank_idx = sk_tokens.index("<extra_id_0>")
    if len(sk_tokens) == len(cor_tokens):
        return cor_tokens[blank_idx], corrected
    matcher = difflib.SequenceMatcher(None, sk_tokens, cor_tokens)
    opcodes = matcher.get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        if i1 <= blank_idx < i2 and j1 < len(cor_tokens):
            return cor_tokens[j1], corrected
    if blank_idx < len(cor_tokens):
        return cor_tokens[blank_idx], corrected
    return None, corrected

def blankify_sentence(corrected, answer):
    tokens = corrected.split()
    try:
        idx = tokens.index(answer)
    except ValueError:
        return None
    tokens[idx] = "___"
    return " ".join(tokens)

# Generate wrong choices from topic pool (harder for Advanced level)
def make_distractors(topic, answer, difficulty):
    pool = [x for x in TOPICS[topic] if x != answer]

    if len(pool) < 3:
        all_words = set(sum(TOPICS.values(), [])) - {answer}
        filler = list(all_words - set(pool))
        random.shuffle(filler)
        pool = pool + filler[: 3 - len(pool)]

    if difficulty == "Basic":
        random.shuffle(pool)
        return pool[:3]

    if difficulty == "Intermediate":
        random.shuffle(pool)
        return pool[:3]

    if difficulty == "Advanced":
        if topic == "tense":
            order = ["go", "goes", "went", "gone"]
            if answer in order:
                idx = order.index(answer)
                cands = []
                if idx > 0:
                    cands.append(order[idx - 1])
                if idx < len(order) - 1:
                    cands.append(order[idx + 1])
                others = [x for x in pool if x not in cands]
                random.shuffle(others)
                cands += others

                if len(cands) < 3:
                    all_words = set(sum(TOPICS.values(), [])) - {answer} - set(cands)
                    filler = list(all_words)
                    random.shuffle(filler)
                    cands += filler[: 3 - len(cands)]

                return cands[:3]

        random.shuffle(pool)
        return pool[:3]

# Generate one MCQ question from learner profile
def make_single_mcq(profile):
    level = profile.get("overall_skill", "Basic")

    if level not in ["Basic", "Intermediate", "Advanced"]:
        level = "Basic"

    topic = select_topic(profile)
    skeleton = random.choice(SKELETONS[topic][level])
    corrected = fill_blank(skeleton)
    answer, corrected = extract_answer(skeleton, corrected)

    if not answer:
        return None
    answer_clean = answer.strip(",.?!;:\"'()")

    if answer_clean not in TOPICS[topic]:
        return None

    question = blankify_sentence(corrected, answer_clean)

    if question is None:
        return None

    distractors = make_distractors(topic, answer_clean, level)

    if distractors is None:
        return None
    
    choices = distractors + [answer_clean]
    random.shuffle(choices)
    correct_index = choices.index(answer_clean)

    return {
        "topic": topic,
        "difficulty": level,
        "question": question,
        "choices": choices,
        "correct_index": correct_index,
        "correct_answer": answer_clean,
        "original_sentence": corrected,
        "explanation": None
    }

def generate_explanation(original_sentence, answer, topic):
    system_prompt = "You are an English tutor. Explain grammar clearly and concisely."
    user_message = f"""
Sentence: {original_sentence}
Correct answer: {answer}
Grammar topic: {topic}

Give a short 1 sentence explanation of why this answer is correct.
Do NOT use headings, bullet points, or markdown.
Keep it concise and clear.
"""

    return call_llm(system_prompt, user_message)

# Generate n questions, retry up to 15x per question if generation fails
def generate_quiz(user, n=5):
    profile = user["profile"]

    quiz = []
    attempts = 0
    max_attempts = n * 15
    
    while len(quiz) < n and attempts < max_attempts:
        q = make_single_mcq(profile)
        attempts += 1

        if q is None:
            continue

        quiz.append(q)
    
    return quiz

