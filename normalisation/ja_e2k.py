import re
from e2k import C2K

c2k = C2K()

def normalise(text: str, source: str = "") -> str:
    # Whitespace strip
    text = re.sub(r'^[\s\u3000]+|[\s\u3000]+$', '', text)
    text = re.sub(r'[\u3000 \t]+', ' ', text)

    # High-level punctuation replacements
    text = text.replace("...", "…")
    text = text.replace("–", "―").replace("—", "―")
    text = text.replace("“", "「").replace("”", "」")
    text = text.replace("‘", "『").replace("’", "』")

    # Convert half-width to full-width Japanese punctuation
    # Only replace . with 。 if it's at the end of a sentence (not in numbers or acronyms)
    text = re.sub(r'(?<!\w)\.(?=\s|$)', '。', text)
    text = re.sub(r',', '、', text)
    text = re.sub(r':', '：', text)
    text = re.sub(r'\?', '？', text)
    text = re.sub(r'!', '！', text)

    # Remove duplicate punctuation
    text = re.sub(r'[。]{2,}', '。', text)
    text = re.sub(r'[、]{2,}', '、', text)
    text = re.sub(r'[？]{2,}', '？', text)
    text = re.sub(r'[！]{2,}', '！', text)
    text = re.sub(r'[…]{2,}', '…', text)

    # Collapse junk before sentence ender
    text = re.sub(r'[、…・]+(?=[。？！]\Z)', '', text)
    text = re.sub(r'[（(]+(?=[。？！]\Z)', '', text)
    text = re.sub(r'([。？！])[^。？！]*\Z', r'\1', text)

    # Handle dangling closing brackets/parentheses
    dangling_pairs = [('）','（'),(')','('),('］','［'),(']','['),('」','「'),('』','『')]
    for closer, opener in dangling_pairs:
        while text.endswith(closer) and text.count(opener) < text.count(closer):
            text = text[:-1]

    # Full-width space after 。 if followed by Kanji/Katakana
    text = re.sub(r'。(?=[一-龯ぁ-ゔァ-ヴー])', '。　', text)

    # Latin/alphanumeric → Katakana conversion
    token_re = re.compile(r'\d+|[A-Za-z][A-Za-z0-9\'’\-]*')

    def latin_to_katakana(match):
        word = match.group(0)
        if not word:
            return ''
        if word.isdigit():
            return word
        # Split letters from numbers for mixed alphanumerics
        parts = re.split(r'(\d+)', word)
        converted = []
        for p in parts:
            if not p:
                continue
            if p.isdigit():
                converted.append(p)
            elif re.match(r'[A-Za-z]+', p):
                converted.append(c2k(p) or p)
            else:
                converted.append(p)
        return ''.join(converted)

    text = token_re.sub(latin_to_katakana, text)

    # Match sentence ender from source
    if source:
        text = match_sentence_ender(source, text)

    return text


def match_sentence_ender(source: str, target: str) -> str:
    source_enders = {'.', '!', '?', '。', '！', '？', '؟', '․', '‽', '⸮', '؛', '۔', '।'}
    japanese_ender_map = {'.':'。','․':'。','!':'！','?':'？','。':'。','！':'！','？':'？','؟':'？','‽':'？','⸮':'？','؛':'。','۔':'。','।':'。'}
    source = source.strip()
    target = target.strip()
    source_punct = source[-1] if source and source[-1] in source_enders else None
    if source_punct:
        mapped = japanese_ender_map.get(source_punct)
        if mapped:
            if not target or target[-1] not in japanese_ender_map.values():
                target += mapped
            elif target[-1] != mapped:
                target = re.sub(r"[。！？]+$", "", target) + mapped
    return target
