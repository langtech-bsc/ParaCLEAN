import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
	text = text.replace("“", '"').replace("”", '"')
	text = text.replace("‘", "'").replace("’", "'")
	text = re.sub(r'(^|\s|\(|\[|{|<)"', r'\1„', text)
	text = re.sub(r'"($|\s|[.,;:!?)}\]>-])', r'”\1', text)
	
	def replace_quote(match):
		quote_pos = match.start()
		# Look backwards for the last „
		before = text[:quote_pos]
		after = text[quote_pos+1:]
		if '„' in before and (before.rfind('„') > before.rfind('“')):
			return '”'  # after an opening quote, treat as closing
		elif '“' in after:
			return '„'  # before a closing quote, treat as opening
		else:
			return '"'  # fallback, leave as straight quote

	# Apply to all remaining straight quotes
	text = re.sub(r'"', replace_quote, text)

	# if source:
	# 	text = match_sentence_ender(source, text)

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