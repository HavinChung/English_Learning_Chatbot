# English Learning Chatbot

A lightweight English-learning platform that provides conversational practice, grammar correction, vocabulary lookup, and adaptive quizzes. The system uses a FastAPI backend, a minimal HTML/JavaScript frontend, and several custom ML components including a fine-tuned T5-small grammar correction model and a local vocabulary RAG module.

## Features

**Chat**
- Multi-session conversation with stored history
- ChatGPT-style interface (HTML/CSS/JS)
- Automatic session titles and summaries
- Integrated grammar explanation and vocabulary lookup

**Grammar Correction**
- Fine-tuned T5-small Seq2Seq model
- Outputs corrected sentence + brief explanation
- FastAPI inference endpoint

**Vocabulary RAG**
- Local dictionary stored in JSON
- Unified schema (word, POS, definition, examples, synonyms)
- Supports multiple POS for the same word

**Quiz System**
- LLM-generated questions with four choices
- Explanations and difficulty levels
- Local storage of quiz attempts
- Review page for past quizzes

## Project Structure

```pipeline
project/
│
├── backend/
│   ├── main.py
│   ├── grammar_model.py
│   ├── vocabulary/
│   │   └── vocab_data.json
│   ├── quiz/
│   │   ├── generator.py
│   │   ├── evaluator.py
│   │   └── sessions/
│   ├── sessions/
│   └── summaries/
│
├── frontend/
│   ├── index.html
│   ├── quiz.html
│   ├── styles.css
│   └── script.js
│
└── models/
    └── t5-small/
```

## Installation
```terminal
pip install fastapi uvicorn transformers sentencepiece torch
```

### Run the server:

```terminal
uvicorn backend.main:app --reload
```
