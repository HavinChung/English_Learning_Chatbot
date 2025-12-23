import pandas as pd
import json
import difflib
import random

# Find diff positions and replace one with <extra_id_0> for T5 training
def make_blank_skeleton(incorrect, correct):
    inc_tokens = incorrect.split()
    cor_tokens = correct.split()
    matcher = difflib.SequenceMatcher(None, inc_tokens, cor_tokens)
    opcodes = matcher.get_opcodes()
    diff_positions = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag != "equal":
            if i1 < len(inc_tokens):
                diff_positions.append(i1)
            elif i2 - 1 < len(inc_tokens):
                diff_positions.append(i2 - 1)
    if not diff_positions:
        return None
    pos = random.choice(diff_positions)
    inc_with_blank = inc_tokens.copy()
    inc_with_blank[pos] = "<extra_id_0>"
    skeleton = " ".join(inc_with_blank)
    return skeleton

# Convert grammar correction pairs to blank-filling format for T5 fine-tuning
def convert_csv_to_blank_json(csv_path, output_path="blank_finetune.json"):
    df = pd.read_csv(csv_path)
    blank_data = []
    for idx, row in df.iterrows():
        incorrect = str(row["source"]).strip()
        correct = str(row["target"]).strip()
        
        incorrect = incorrect.replace('"', '').replace("'", '')
        correct = correct.replace('"', '').replace("'", '')
        
        skeleton = make_blank_skeleton(incorrect, correct)
        if skeleton is None:
            continue
        blank_data.append({
            "input": skeleton,
            "output": correct
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blank_data, f, indent=2, ensure_ascii=False)

convert_csv_to_blank_json("grammar_train.csv")