import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
    # Normalize all quote variants to standard double quotes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("„", '"').replace("«", '"').replace("»", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("…", "...")

    # # Match sentence-ending punctuation to source if needed
    # if source:
    #     text = match_sentence_ender(source, text)

    return text


def match_sentence_ender(source: str, target: str) -> str:

    target_ender_map = {
        '.': '.', '!': '!', '?': '?'
    }

    source = source.strip()
    target = target.strip()

    if not source:
        return target

    source_punct = source[-1]
    mapped = target_ender_map.get(source_punct)
    if not mapped:
        return target

    # Remove any trailing punctuation (Unicode punctuation)
    while target and unicodedata.category(target[-1]).startswith('P'):
        target = target[:-1]

    # Append mapped punctuation if not already present
    if not target.endswith(mapped):
        target += mapped

    return target
