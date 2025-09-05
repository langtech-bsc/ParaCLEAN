import re
import unicodedata


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

	text = (
		text.replace("“", '«')
			.replace("”", '»')
			.replace("‘", "'")
			.replace("’", "'")
	)
	NBSP = "\u00A0"
	# safe quote normalisation - only looking at single balanced pairs
	if text.count('"') == 2 and "«" not in text and "»" not in text:
		# replace the single balanced pair
		def _replace_quotes(m):
			inner = m.group(1).strip()
			return f"«{NBSP}{inner}{NBSP}»"
		text = re.sub(r'"([^"\n]+)"', _replace_quotes, text, count=1)

	# def protect_urls(text):
	# 	urls = []
	# 	def repl(match):
	# 		urls.append(match.group(0))
	# 		return f"__URL{len(urls)-1}__"
	# 	return re.sub(r"(https?|ftp|mailto):[^\s]+", repl, text), urls

	# def restore_urls(text, urls):
	# 	for i, url in enumerate(urls):
	# 		text = text.replace(f"__URL{i}__", url)
	# 	return text

	# text, urls = protect_urls(text)

	text = re.sub(r"(?<!\d)\s*([!?;:]+(?!\d))(?=(\s|[A-Za-zÀ-ÿ]|$))", NBSP + r"\1", text)

	# text = restore_urls(text, urls)

	text = re.sub(r'«\s*', '«' + NBSP, text)   # space after opening
	text = re.sub(r'\s*»', NBSP + '»', text)  # space before closing

	# -------------------------------------------------
	# Step 2: Restore protected tokens
	# -------------------------------------------------
	for k, v in protected.items():
		text = text.replace(k, v)

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