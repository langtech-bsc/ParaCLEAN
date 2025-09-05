import re
import unicodedata

def normalise(text: str, source: str = "") -> str:

    # Normalize quotation marks and apostrophes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    # # Numbers: convert decimal point → comma
    # text = re.sub(r"(\d)\.(\d)", r"\1,\2", text)

    # # Numbers: convert thousands separator from , or . → NBSP
    # text = re.sub(r"(\d)[,.](?=\d{3}\b)", lambda m: m.group(1) + "\u00A0", text)

    # if source:
    #     text = match_sentence_ender(source, text)

    return text


def match_sentence_ender(source: str, target: str) -> str:
    # Set of known sentence-ending punctuation marks across languages
    source_enders = {'.', '!', '?', '。', '！', '？', '؟', '․', '‽', '⸮', '؛', '।'}

    # Canonical end punctuation for general non-CJK targets
    target_ender_map = {
        '.': '.',
        '!': '!',
        '?': '?',
        '。': '.',
        '！': '!',
        '？': '?',
        '؟': '?',
        '।': '.',  
    }

    source = source.strip()
    target = target.strip()

    source_punct = source[-1] if source and source[-1] in source_enders else None

    if source_punct:
        mapped = target_ender_map.get(source_punct)
        if mapped:
            if not target or target[-1] not in target_ender_map.values():
                target += mapped
            elif target[-1] != mapped:
                target = re.sub(r"[.!?]+$", "", target) + mapped

    return target
