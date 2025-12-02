import json

class VocabStore:
    def __init__(self, vocab_path="vocab_data.json"):
        self.vocab_path = vocab_path
        self.entries = []
        self.index_by_word = {}

        self.load()

    def load(self):
        with open(self.vocab_path, "r", encoding="utf-8") as f:
            self.entries = json.load(f)

        index = {}
        for entry in self.entries:
            word = entry["word"].lower()
            if word not in index:
                index[word] = []
            index[word].append(entry)

        self.index_by_word = index

    def lookup(self, word, pos=None):
        key = word.lower()
        if key not in self.index_by_word:
            return []

        entries = self.index_by_word[key]

        if pos is None:
            return entries
        
        filtered = []
        for e in entries:
            if e.get("pos") == pos:
                filtered.append(e)
            
        return filtered

    def search_substring(self, text):
        text_lower = text.lower()
        results = []

        for entry in self.entries:
            if text_lower in entry["word"].lower():
                results.append(entry)

        return results

if __name__ == "__main__":
    store = VocabStore()
