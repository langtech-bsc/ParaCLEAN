import re
import unicodedata

# def normalise(text: str, source: str = "") -> str:
#     text = unicodedata.normalize("NFKC", text)
#     text = text.strip()
#     text = re.sub(r"[ \t]+", " ", text)  # collapse ASCII whitespace only
#     text = text.replace("–", "-").replace("—", "-")
#     text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
#     text = re.sub(r"[^\x20-\x7E\u00A0-\uFFFF]", "", text)

#     if source:
#         text = match_sentence_ender(source, text)

#     return text

import unicodedata
import re

def normalise(text: str, source: str = "") -> str:
	# Canonical Unicode form
	text = unicodedata.normalize("NFKC", text)

	# Strip leading/trailing whitespace
	text = text.strip()

	# collapse ASCII whitespace only
	text = re.sub(r"[ \t]+", " ", text) 

	# Standardise dashes and hyphens
	text = text.replace("–", "-").replace("—", "-")
	text = text.replace("−", "-").replace("\u2011", "-")  # minus sign + non-breaking hyphen

	# Standardise quotes
	text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

	# Remove invisible / control characters (zero-width space, joiners, etc.)
	text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
	text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

	# Match sentence end punctuation if source is given
	if source:
		text = match_sentence_ender(source, text)

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
		'؟': '?',
		'।': '.',  
	}

	source = source.strip()
	target = target.strip()

	# Determine end punctuation in source
	source_punct = source[-1] if source and source[-1] in source_enders else None

	if source_punct:
		# Get canonical punctuation for the target
		mapped = target_ender_map.get(source_punct)
		if mapped:
			# If target ends in anything other than the expected punctuation, fix it
			if not target or target[-1] not in target_ender_map.values():
				target += mapped
			elif target[-1] != mapped:
				target = re.sub(r"[.!?]+$", "", target) + mapped

	return target