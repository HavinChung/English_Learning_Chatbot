import json

def normalize_cambridge(data):
    corpus = []
    for sense_list in data:
        for item in sense_list:
            corpus.append({
                "word": item["word"],
                "pos": item.get("part_of_speech", None),
                "definition": item["definition"],
                "examples": item.get("examples", []),
                "synonyms": [],
                "source": "cambridge"
            })
    return corpus


def normalize_wordnet(data):
    corpus = []
    for item in data:
        corpus.append({
            "word": item["word"],
            "pos": item.get("pos", None),
            "definition": item["definition"],
            "examples": item.get("examples", []),
            "synonyms": item.get("synonyms", []),
            "source": "wordnet"
        })
    return corpus


def main():
    cambridge_path = "cambridge_final_results_cleaned.json"
    wordnet_path = "wordnet_word_data.json"
    output_path = "vocab_data.json"

    with open(cambridge_path, "r", encoding="utf-8") as f:
        cambridge_raw = json.load(f)

    with open(wordnet_path, "r", encoding="utf-8") as f:
        wordnet_raw = json.load(f)

    cambridge_entries = normalize_cambridge(cambridge_raw)
    wordnet_entries = normalize_wordnet(wordnet_raw)

    corpus = cambridge_entries + wordnet_entries

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
