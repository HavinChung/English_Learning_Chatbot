import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Vocabulary database with exact lookup and TF-IDF semantic search
class VocabStore:
    def __init__(self, vocab_path: str = "vocab_data.json"):
        self.vocab_path = vocab_path
        self.entries = []
        self.index_by_word = {}
        self.vectorizer = None
        self.tfidf_matrix = None
        self.documents = []
        self.load()
        self.build_tfidf_index()

    def load(self):
        with open(self.vocab_path, "r", encoding="utf-8") as f:
            self.entries = json.load(f)

        index = {}
        for entry in self.entries:
            word = str(entry.get("word", "")).lower()
            index.setdefault(word, []).append(entry)
        self.index_by_word = index

    # Build TF-IDF vectors from word, definition, synonyms, examples
    def build_tfidf_index(self):
        self.documents = []
        for entry in self.entries:
            parts = [
                str(entry.get("word", "")),
                str(entry.get("definition", "")),
                " ".join(entry.get("synonyms", [])) if isinstance(entry.get("synonyms", []), list) else str(entry.get("synonyms", "")),
                " ".join(entry.get("examples", [])) if isinstance(entry.get("examples", []), list) else str(entry.get("examples", "")),
            ]
            self.documents.append(" ".join(parts).lower())

        self.vectorizer = TfidfVectorizer(
            max_features=None,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

    # Exact word match (optionally filtered by part of speech)
    def lookup(self, word: str, pos: str = None):
        key = str(word).lower()
        if key not in self.index_by_word:
            return []
        entries = self.index_by_word[key]
        if pos is None:
            return entries
        return [e for e in entries if e.get("pos") == pos]

    def search_substring(self, text: str):
        text_lower = str(text).lower()
        return [e for e in self.entries if text_lower in str(e.get("word", "")).lower()]

    # Semantic search using cosine similarity; falls back to substring if no results
    def search_tfidf(self, query: str, top_k: int = 5, threshold: float = 0.0):
        if self.vectorizer is None or self.tfidf_matrix is None:
            return self.search_substring(query)

        query_vec = self.vectorizer.transform([str(query).lower()])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] >= threshold:
                entry = self.entries[idx].copy()
                entry["similarity_score"] = float(similarities[idx])
                results.append(entry)

        return results if results else self.search_substring(query)

    # Try exact match first, then TF-IDF, then substring
    def smart_search(self, query: str):
        exact = self.lookup(query)
        if exact:
            return exact
        tfidf_res = self.search_tfidf(query, top_k=3)
        if tfidf_res:
            return tfidf_res
        return self.search_substring(query)


if __name__ == "__main__":
    store = VocabStore("data/vocab_data.json")