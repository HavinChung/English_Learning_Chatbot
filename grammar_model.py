import os
from datasets import load_from_disk
from transformers import T5Tokenizer, T5ForConditionalGeneration, DataCollatorForSeq2Seq, TrainingArguments, Trainer

# Trained over 200,000 data points of grammar correction pairs

MODEL_NAME = "t5-small"
MAX_INPUT_LENGTH = 128
MAX_TARGET_LENGTH = 128


def load_dataset(data_dir="data/grammar_correction_pairs"):
    dataset = load_from_disk(data_dir)
    print(dataset)
    return dataset


def get_tokenizer_and_model():
    tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    return tokenizer, model


def preprocess_function(examples, tokenizer):
    inputs = []

    for sentence in examples["source"]:
        inputs.append("grammar: " + sentence)

    targets = examples["target"]

    model_inputs = tokenizer(
        inputs,
        max_length=MAX_INPUT_LENGTH,
        truncation=True,
    )

    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets,
            max_length=MAX_TARGET_LENGTH,
            truncation=True,
        )

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def main():
    raw_datasets = load_dataset()

    tokenizer, model = get_tokenizer_and_model()

    tokenized_datasets = raw_datasets.map(
        lambda batch: preprocess_function(batch, tokenizer),
        batched=True,
        remove_columns=["source", "target"],
    )

    train_dataset = tokenized_datasets["train"]
    eval_dataset = tokenized_datasets["test"]

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
    )

    output_dir = "models/t5-grammar-small"

    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="steps",
        eval_steps=2000,
        logging_steps=200,
        save_steps=2000,
        save_total_limit=2,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=1,
        learning_rate=3e-4,
        weight_decay=0.01,
        warmup_steps=1000,
        report_to="none",
        fp16=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    trainer.train()

    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)


if __name__ == "__main__":
    main()