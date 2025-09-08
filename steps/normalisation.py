from pathlib import Path
import importlib
from normalisation.core import core_normalise

def get_normaliser(lang_code):
    """Dynamically load a normaliser for a given language, fallback to default."""
    try:
        lang_module = importlib.import_module(f"normalisation.{lang_code}")
    except ImportError:
        lang_module = importlib.import_module("normalisation.default")

    def normalise(text: str, source: str = "") -> str:
        text = core_normalise(text, source)
        if hasattr(lang_module, "normalise"):
            text = lang_module.normalise(text, source)
        return text

    return normalise


def apply_normalisation(input_path, output_path, l1, l2, with_header=True):
    """
    Read 2-column TSV (l1, l2) from file, 
    write 4-column TSV (l1_orig, l1_norm, l2_orig, l2_norm) to file.
    """
    l1_norm = get_normaliser(l1)
    l2_norm = get_normaliser(l2)

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        if with_header:
            outfile.write("l1_orig\tl1_norm\tl2_orig\tl2_norm\n")

        for line_number, line in enumerate(infile, start=1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                print(f"[Warning] Skipping malformed line {line_number}: {line.strip()}")
                continue

            l1_sent, l2_sent = parts[0], parts[1]
            norm_l1 = l1_norm(l1_sent, source=l2_sent)
            norm_l2 = l2_norm(l2_sent, source=l1_sent)

            outfile.write(f"{l1_sent}\t{norm_l1}\t{l2_sent}\t{norm_l2}\n")

    return output_path