import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Fine-tuned T5 model for grammar correction
MODEL_PATH = "models/t5-grammar-small"

# Lazy loading to avoid loading on import
tokenizer = None
model = None

# Load model only once when first needed
def load_model():
    global tokenizer, model

    if tokenizer is None or model is None:
        tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
        model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)
        model.eval()

    return tokenizer, model

# Correct grammar using T5 model with beam search
def correct_grammar(sentence: str) -> str:
    tokenizer, model = load_model()

    # T5 expects task prefix
    input_text = "grammar: " + sentence

    inputs = tokenizer.encode(
        input_text,
        return_tensors="pt",
        truncation=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=128,
            num_beams=4,
            early_stopping=True
        )

    corrected = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return corrected
