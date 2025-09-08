import re

def match_sentence_ender(source: str, target: str) -> str:
	japanese_ender_map = {'.':'。','!':'！','?':'？','。':'。','！':'！','？':'？'}
	if not source or not target:
		return target
	source_last = source.strip()[-1]
	target_last = target.strip()[-1]
	mapped = japanese_ender_map.get(source_last)
	if mapped and not re.match(r'[。！？a-zA-Z0-9,、]', target_last):
		if target.endswith("…"):
			return target
		elif target.endswith("."):
				target = re.sub(r"\.$", "。", target)
		enders_class = re.escape("".join(japanese_ender_map.values()))
		if not target or target[-1] not in japanese_ender_map.values():
			target += mapped
		elif target[-1] != mapped:
			target = re.sub(r"[" + enders_class + r"]+$", "", target) + mapped
	return target

# def normalise(text: str, source: str = "") -> str:
#     # Strip whitespace
#     text = text.strip()
#     text = re.sub(r'[\u3000 \t]+', ' ', text)

#     # High-level punctuation
#     text = text.replace("...", "…").replace("–", "―").replace("—", "―")
#     text = text.replace("“", "「").replace("”", "」")
#     text = text.replace("‘", "『").replace("’", "』")

#     # Periods
#     text = re.sub(r'(?<![A-Za-z0-9])\.(?![A-Za-z0-9、,])', '。', text)

#     # Commas: only replace if NOT between digits (ASCII or full-width)
#     new_text = []
#     for i, ch in enumerate(text):
#         if ch == ',':
#             left = text[i-1] if i > 0 else ''
#             right = text[i+1] if i < len(text)-1 else ''
#             if left.isdigit() and right.isdigit():
#                 new_text.append(',')  # preserve numeric comma
#             else:
#                 new_text.append('、')  # replace textual comma
#         else:
#             new_text.append(ch)
#     text = ''.join(new_text)

#     # Other punctuation
#     text = text.replace('?', '？').replace('!', '！')

#     # Colon handling
#     # Step 1: protect URI schemes (http:, https:, ftp:, mailto:, etc.)
#     # Temporarily replace them with a placeholder
#     text = re.sub(r'([A-Za-z][A-Za-z0-9+.-]*):', r'\1<<COLON>>', text)

#     # Step 2: protect times like 14:30
#     text = re.sub(r'(\d):(\d)', r'\1<<COLON>>\2', text)

#     # Step 3: convert any remaining ":" to full-width
#     text = text.replace(':', '：')

#     # Step 4: restore protected colons
#     text = text.replace('<<COLON>>', ':')

#     return text

import re

def normalise(text: str, source: str = "") -> str:
    # Dictionary to hold protected tokens
    protected = {}

    def _protect(pattern, tag):
        nonlocal text
        def repl(m):
            key = f"<<{tag}{len(protected)}>>"
            protected[key] = m.group(0)
            return key
        text = re.sub(pattern, repl, text)

    # -------------------------------------------------
    # Step 0: Protect fragile tokens
    # -------------------------------------------------

    # URLs: http, https, ftp, file, mailto
    _protect(r'\b(?:https?|ftp|file|mailto):[^\s]+', "URL")

    # Windows paths like C:\Users\...
    _protect(r'[A-Za-z]:\\[^\s]+', "WINPATH")

    # C++ double colons
    _protect(r'::', "DCOLON")

    # Emoticons like :-) ;-) :D :-P =O etc.
    _protect(r'[:;=8][\-^oO\']?[)DPpOo(\/|3\]\[]', "EMOJI")

    # Times like 06:00, 14:30
    _protect(r'\b\d{1,2}:\d{2}\b', "TIME")

    # -------------------------------------------------
    # Step 1: Normalize remaining text
    # -------------------------------------------------

    # Strip whitespace
    text = text.strip()
    text = re.sub(r'[\u3000 \t]+', ' ', text)

    # High-level punctuation
    text = text.replace("...", "…").replace("–", "―").replace("—", "―")
    text = text.replace("“", "「").replace("”", "」")
    text = text.replace("‘", "『").replace("’", "』")

    # Periods
    text = re.sub(r'(?<![A-Za-z0-9])\.(?![A-Za-z0-9、,])', '。', text)

    # Commas: only replace if NOT between digits
    new_text = []
    for i, ch in enumerate(text):
        if ch == ',':
            left = text[i-1] if i > 0 else ''
            right = text[i+1] if i < len(text)-1 else ''
            if left.isdigit() and right.isdigit():
                new_text.append(',')  # preserve numeric comma
            else:
                new_text.append('、')  # replace textual comma
        else:
            new_text.append(ch)
    text = ''.join(new_text)

    # Replace ? and ! with full-width
    text = text.replace('?', '？').replace('!', '！')

    # Replace : with full-width (colons in protected tokens remain safe)
    text = text.replace(':', '：')

    # -------------------------------------------------
    # Step 2: Restore protected tokens
    # -------------------------------------------------
    for k, v in protected.items():
        text = text.replace(k, v)

    return text