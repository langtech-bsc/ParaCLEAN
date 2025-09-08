import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
	# Protect ellipses
	text = text.replace("…", "<ELLIPSIS>")
	text = re.sub(r'\.\.+', r'<ELLIPSIS>', text)

	# 1) Protect list markers like "1." "2." "5."
	text = re.sub(r'(\d+)\.(\s)', r'\1.<KEEP>\2', text)

	# 2) Replace genuine sentence-final periods with danda
	# (not decimals, not abbreviations)
	text = re.sub(r'(?<!\d)\.(?=$|\s+[A-Z\u0900-\u097F])', '।', text)

	# 3) Restore list markers
	text = text.replace('.<KEEP>', '.')

	# Replace trailing pipes
	text = re.sub(r"\|+$", '।', text)

	# Restore ellipses
	text = text.replace("<ELLIPSIS>।", "...").replace("<ELLIPSIS>", "...")
	# Convert Devanagari digits to ASCII
	devanagari_digits = "०१२३४५६७८९"
	for i, d in enumerate(devanagari_digits):
		text = text.replace(d, str(i))

	# if source:
	# 	text = match_sentence_ender(source, text)

	return text


def match_sentence_ender(source: str, target: str) -> str:
	# Known sentence-ending punctuation
	source_enders = {'.', '!', '?', '。', '！', '？', '؟', '․', '‽', '⸮', '؛', '।'}

	# Canonical end punctuation mapping
	target_ender_map = {
		'.': '।',
		'!': '!',
		'?': '?',
		'。': '।',
		'！': '!',
		'？': '?',
		'؟': '?',
		'।': '।',
	}

	source = source.strip()
	target = target.strip()

	source_punct = source[-1] if source and source[-1] in source_enders else None

	if source_punct:
		mapped = target_ender_map.get(source_punct)
		if mapped:
			# Leave ellipses untouched
			if target.endswith("..."):
				return target
			elif target.endswith("."):
				target = re.sub(r"\.$", "।", target)

			# If target doesn't end in correct punctuation, fix it
			enders_class = re.escape("".join(target_ender_map.values()))
			if not target or target[-1] not in target_ender_map.values():
				target += mapped
			elif target[-1] != mapped:
				target = re.sub(r"[" + enders_class + r"]+$", "", target) + mapped

	return target
