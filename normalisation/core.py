import re
import unicodedata

def core_normalise(text: str, source: str = "") -> str:
	# Canonical Unicode form
	text = unicodedata.normalize("NFC", text)

	# Strip leading/trailing whitespace
	text = text.strip()

	# Collapse ASCII whitespace only
	text = re.sub(r"[ \t]+", " ", text)

	# Remove invisible / control characters
	text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
	text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

	return text