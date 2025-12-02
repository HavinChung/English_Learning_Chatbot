import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration

MODEL_PATH = "models/t5-grammar-small"

_tokenizer = None
_model = None

def load_model():
    global _tokenizer, _model

    if _tokenizer is None or _model is None:
        _tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
        _model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)
        _model.eval()

    return _tokenizer, _model


def correct_grammar(sentence: str) -> str:
    tokenizer, model = load_model()

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
