import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
    # Normalize quotation marks to guillemets
    text = (
        text.replace("“", "«")
            .replace("”", "»")
            .replace("„", "«")
            .replace("«", "«")
            .replace("»", "»")
            .replace('"', '"')  # keep as placeholder for regex step
            .replace("‘", "'")
            .replace("’", "'")
    )

    # Safe quote normalisation - only looking at single balanced pairs
    if text.count('"') == 2 and "«" not in text and "»" not in text:
        def _replace_quotes(m):
            inner = m.group(1).strip()
            return f"«{inner}»"   # no spacing in Norwegian
        text = re.sub(r'"([^"\n]+)"', _replace_quotes, text, count=1)

    # Replace any leftover straight quotes in pairs
    # (best-effort fallback if there are more than 2)
    while text.count('"') >= 2:
        text = text.replace('"', '«', 1)
        text = text.replace('"', '»', 1)

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
