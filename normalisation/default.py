import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
    # Standardise quotes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # # Match sentence end punctuation if source is given
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

    # Determine end punctuation in source
    source_punct = source[-1] if source and source[-1] in source_enders else None
    mapped = target_ender_map.get(source_punct) if source_punct else None

    if mapped:
        if not target:
            target = mapped
        elif target[-1] != mapped:
            # Remove any known punctuation at the end before appending the mapped one
            target = re.sub(r"[{}]+$".format(re.escape(''.join(target_ender_map.keys()))), "", target)
            target += mapped

    return target
