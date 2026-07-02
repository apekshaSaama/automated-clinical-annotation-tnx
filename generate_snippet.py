from __future__ import annotations

import argparse
import re
from dataclasses import dataclass

SMOKING_KEYWORDS = [
    r"smok\w*",
    r"tobacco",
    r"cigarette\w*",
    r"cigar\w*",
    r"nicotine",
    r"vap\w*",
    r"e-cigarette\w*",
    r"pack[- ]year\w*",
    r"chew(?:ing|ed)?\s+tobacco",
    r"snuff",
]

SMOKING_PATTERN = re.compile(r"\b(?:" + "|".join(SMOKING_KEYWORDS) + r")\b", re.IGNORECASE)

SENTENCE_PATTERN = re.compile(r"[^.!?\n]+(?:[.!?]+|\n|$)")


@dataclass
class Snippet:
    text: str
    start: int
    end: int


def _iter_sentences(note_text: str):
    for match in SENTENCE_PATTERN.finditer(note_text):
        sentence = match.group()
        if sentence.strip():
            yield sentence, match.start()


def extract_smoking_snippets(note_text: str) -> list[Snippet]:
    if not note_text or not note_text.strip():
        return []

    snippets: list[Snippet] = []
    for sentence, sentence_start in _iter_sentences(note_text):
        if not SMOKING_PATTERN.search(sentence):
            continue
        stripped = sentence.strip()
        offset = sentence.index(stripped)
        start = sentence_start + offset
        snippets.append(Snippet(text=stripped, start=start, end=start + len(stripped)))
    return snippets


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract smoking-related snippets from a clinical note")
    parser.add_argument("--file", dest="file_path", required=True, help="Path to a text file containing the clinical note")
    args = parser.parse_args()

    with open(f"notes/smoking/{args.file_path}", "r", encoding="utf-8") as handle:
        note_text = handle.read()

    snippets = extract_smoking_snippets(note_text)
    if not snippets:
        print("No smoking-related snippets found.")
        return

    for snippet in snippets:
        print(f"[{snippet.start}-{snippet.end}] {snippet.text}")
    #store snippet in a file with path smoking_snippets/filename.txt
    with open(f"smoking_snippets/{args.file_path}.txt", "w", encoding="utf-8") as handle:
        for snippet in snippets:
            handle.write(f"[{snippet.start}-{snippet.end}] {snippet.text}\n")
if __name__ == "__main__":
    main()
