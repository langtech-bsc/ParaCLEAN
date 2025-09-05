import os
import random
from pathlib import Path

BASE_DIR = "/gpfs/projects/bsc88/data/04-mt-samplings"
OUTPUT_DIR = "testing_data"
SAMPLE_SIZE = 5000

os.makedirs(OUTPUT_DIR, exist_ok=True)

sampled_languages = {f.stem for f in Path(OUTPUT_DIR).glob("*.txt")}

def sample_lines(lines, n):
    """Randomly sample up to n lines from list of lines."""
    if len(lines) <= n:
        return lines
    return random.sample(lines, n)

def process_file(filepath):
    filename = os.path.basename(filepath)
    langs_part = filename.split(".")[-1]  # e.g., 'en', 'ru', 'en-ru'
    
    if "-" in langs_part:  # TSV with two languages
        return
    
    else:  # Single language file
        lang = langs_part
        if lang in sampled_languages:
            return
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.rstrip("\n") for line in f]
        sampled = sample_lines(lines, SAMPLE_SIZE)
        out_path = Path(OUTPUT_DIR) / f"{lang}.txt"
        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write("\n".join(sampled))
        sampled_languages.add(lang)

# Walk through directory and process files
for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".txt") or "." in file:  # crude filter, adjust if needed
            filepath = os.path.join(root, file)
            process_file(filepath)

print(f"✅ Sampling complete. Output saved in '{OUTPUT_DIR}'")
