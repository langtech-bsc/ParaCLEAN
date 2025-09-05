import unicodedata
import re

def normalise(text: str, source: str = "") -> str:
    # --- URL protection helpers ---
    def protect_urls(text):
        urls = []
        def repl(match):
            urls.append(match.group(0))
            return f"__URL{len(urls)-1}__"
        return re.sub(r"(https?|ftp|mailto):[^\s]+", repl, text), urls

    def restore_urls(text, urls):
        for i, url in enumerate(urls):
            text = text.replace(f"__URL{i}__", url)
        return text

    # Protect URLs
    text, urls = protect_urls(text)

    # Normalize quotation marks and apostrophes to ASCII
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    # First handle ellipses explicitly
    text = re.sub(r"[。．｡]{3,}", "...", text)   # CJK ellipsis dots
    text = re.sub(r"[…]", "...", text)          # Unicode ellipsis char

    # Map punctuation, but preserve digits
    punct_map = {
        '۔': '.', '․': '.', '。': '.', '｡': '.', '．': '.',  # full stops
        ';': '؛',
        '?': '؟',
        '？': '؟',
        '!': '!',
        '！': '!',
    }

    # Replace punctuation char by char, except commas
    text = ''.join(punct_map.get(c, c) for c in text)

    # Replace commas not between digits with Arabic comma
    text = re.sub(r'(?<!\d),(?!\d)', '،', text)

    # Restore URLs
    text = restore_urls(text, urls)

    return text


# def normalise(text: str, source: str = "") -> str:
#     # Normalize quotation marks and apostrophes to ASCII
#     text = text.replace("“", '"').replace("”", '"')
#     text = text.replace("‘", "'").replace("’", "'")

#     # First handle ellipses explicitly
#     text = re.sub(r"[。．｡]{3,}", "...", text)   # CJK ellipsis dots
#     text = re.sub(r"[…]", "...", text)          # Unicode ellipsis char

#     # Map punctuation, but preserve digits
#     punct_map = {
#         '۔': '.', '․': '.', '。': '.', '｡': '.', '．': '.',  # full stops
#         ';': '؛',
#         '?': '؟',
#         '？': '؟',
#         '!': '!',
#         '！': '!',
#     }

#     # Replace punctuation char by char, except commas
#     text = ''.join(punct_map.get(c, c) for c in text)

#     # Replace commas not between digits with Arabic comma
#     text = re.sub(r'(?<!\d),(?!\d)', '،', text)

#     return text


def match_sentence_ender_arabic(source: str, target: str) -> str:
    target_ender_map = {
        '.': '.', '؟': '؟', '!': '!', '！': '!', '?': '؟'
    }

    source = source.strip()
    target = target.strip()
    if not source:
        return target

    source_punct = source[-1]
    mapped = target_ender_map.get(source_punct)
    if not mapped:
        return target

    # find run of punctuation at target end
    i = len(target)
    while i > 0 and unicodedata.category(target[i-1]).startswith('P'):
        i -= 1
    run = target[i:]

    if not run:
        return target + mapped

    # If run is made of dots (any kind), preserve length as ASCII dots
    if all(ch in {'.', '…', '。', '．', '｡', '․', '۔'} for ch in run):
        return target[:i] + "." * len(run)

    # If run already matches mapped punctuation, keep it
    if all(ch == mapped for ch in run):
        return target

    # Otherwise, normalize each char
    normalized_run = ''.join(target_ender_map.get(ch, ch) for ch in run)
    return target[:i] + normalized_run
