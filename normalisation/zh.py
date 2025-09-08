import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
	protected = {}

	def _protect(pattern, tag):
		nonlocal text
		def repl(m):
			key = f"<<{tag}{len(protected)}>>"
			protected[key] = m.group(0)
			return key
		text = re.sub(pattern, repl, text)

	# Protect URLs (http, https, ftp, file, mailto)
	_protect(r'\b(?:https?|ftp|file|mailto):[^\s]+', "URL")

	# Protect Windows paths like C:\Users\...
	_protect(r'[A-Za-z]:\\[^\s]+', "WINPATH")

	# Protect C++ double colons
	_protect(r'::', "DCOLON")

	# Protect emoticons like :-) ;-) :D :-P =O etc.
	_protect(r'[:;=8][\-^oO\']?[)DPpOo(\/|3\]\[]', "EMOJI")

	# -------------------------------------------------
	# Now do safe normalization on the remaining text
	# -------------------------------------------------

	# Remove leading/trailing whitespace and full-width spaces
	text = text.strip().replace("\u3000", " ")

	# Remove unnecessary ASCII spaces within text (not between Chinese chars)
	# remove spaces between Chinese chars
	text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)

	# normalize the elements in a list
	text = re.sub(r'^(一|二|三|四|五|六|七|八|九|十)\.', r'\1、', text)
	
	# Replace half-width punctuation with full-width Chinese equivalents
	text = text.replace(";", "；")
	text = text.replace("?", "？").replace("!", "！")
	# Replace ellipsis
	text = re.sub(r'(…{1,6}|\.{3,6}|·{6})', '……', text)
	# Replace . after Chinese characters with the Chinese period
	text = re.sub(r'(?<=[\u4e00-\u9fff])\.(?!\w)', '。', text)
	# Further replace periods (.) only if they are not part of initials, numbers, or technical terms like U.S. 3.14
	# Use negative lookbehind and lookahead to exclude such cases
	text = re.sub(r'(?<![A-Za-z0-9])\.(?![A-Za-z0-9])', '。', text)
	# Replace commas not between digits, also cases like "他们称之为X17,因为他们计算出其质量为17兆电子伏。"    
	text = re.sub(r'(?<!\d),|,(?!\d)', '，', text)
	# Replace colons (:) only if they are not part of time notations or ratios
	# This uses a negative lookbehind for digits and a negative lookahead for digits, ensuring colons used in time or ratio contexts are not replaced
	text = re.sub(r'(?<!\d):(?!\d)|(?<=\d):(?=[\u4e00-\u9fff])', '：', text)
	text = re.sub(r'(https?)：//', r'\1://', text, flags=re.IGNORECASE)
	text = re.sub(r'ftp：//', 'ftp://', text, flags=re.IGNORECASE)
	
	
	# Replace ASCII quotation marks with Chinese quotes
	text = text.replace('"', '”')  # default to closing if unsure of context
	text = text.replace("'", "’")

	text = re.sub(r'^”', '“', text)

	if text.count('”') == 2 and '“' not in text:
	   text = text.replace('”', '“', 1)

	if text.count('’') == 2 and '‘' not in text:
		text = text.replace('’', '‘', 1)

	
	# Replace brackets
	text = text.replace("(", "（").replace(")", "）")

	# Replace 「 with Chinese opening quote and 」 with Chinese closing quote
	text = text.replace('「', '“')
	text = text.replace('」', '”') 
	
	text = text.replace('『', '“')
	text = text.replace('』', '”')

	if '«' in text and '»' in text:    
		text = re.sub(r'«\s*', '“', text)
		text = re.sub(r'\s*»', '”', text)


	# Replace extra single dashes with Chinese equivalents
	text = text.replace("–", "——").replace("—", "——")
	# Replace multiple consecutive dashes with a single em dash
	text = re.sub(" - ", "——", text)
	text = re.sub(r'(\s*——\s*){2,}', '——', text)
	text = re.sub(r'—{2,}', '——', text)
	

	# Correct the use of a slight-pause mark used to set off items in a series
	text = re.sub(r'(?<=[\u4e00-\u9fff])丶(?=[\u4e00-\u9fff])', '、', text)

	# correct the · between names
	text = re.sub(r'(?<=[\u4e00-\u9fff])•(?=[\u4e00-\u9fff])', '·', text)

	# remove spaces between Chinese chars and punctuations and digits
	text = re.sub(r'(?<=[\u4e00-\u9fff\w，。！？；：“”‘’（）"《》(……)(——)%])\s+(?=[，。！？；：“”‘’（）"《》%(……)(——)])', '', text)
	text = re.sub(r'(?<=[，。！？；：“”‘’"（）%《》(……)(——)])\s+(?=[\u4e00-\u9fff\w，。！？；：“”‘’（）"《》%(……)(——)])', '', text)
	text = re.sub(r'(\d+)\s+([\u4e00-\u9fff])', r'\1\2', text)
	text = re.sub(r'([\u4e00-\u9fff])\s+(\d+)', r'\1\2', text)
	text = re.sub(r'([A-Za-z0-9])\s+([\u4e00-\u9fff])', r'\1\2', text)
	text = re.sub(r'([\u4e00-\u9fff])\s+([A-Za-z0-9])', r'\1\2', text)    
	# reduce extra spaces
	text = re.sub(r'[ \t]+', ' ', text)

	# -------------------------------------------------
	# Restore protected tokens
	# -------------------------------------------------
	for k, v in protected.items():
		text = text.replace(k, v)

	# Remove control characters and invalid Unicode ranges
	#text = re.sub(r"[^\u4E00-\u9FFF\u3000-\u303F\uFF00-\uFFEF\u4DC0-\u4DFF\u2000-\u206F\u2E80-\u2EFF\u3400-\u4DBF\w\s]", "", text)

	# Optionally fix final punctuation to match source sentence
	# if source:
	#     text = match_sentence_ender(source, text)

	return text


def match_sentence_ender(source: str, target: str) -> str:
	# Sentence-ending punctuation across languages
	source_enders = {'.', '!', '?', '。', '！', '？', '؟', '․', '‽', '⸮', '؛', '。', '！', '？', '।'}

	# Mapping source punctuation to Chinese equivalents
	chinese_ender_map = {
		'.': '。',
		'․': '。',
		'!': '！',
		'?': '？',
		'。': '。',
		'！': '！',
		'？': '？',
		'؟': '？',
		'‽': '？',
		'⸮': '？',
		'؛': '。',  # Semicolon → sentence end (neutral handling)
		'۔': '。',  # Arabic full stop
		'۔': '。',  # Urdu full stop
		'।': '。',   # Devanagari danda
		',': '，'
	}

	source = source.strip()
	target = target.strip()

	source_punct = source[-1] if source and source[-1] in source_enders else None

	if source_punct:
		mapped = chinese_ender_map.get(source_punct)
		if mapped:
			if not target or target[-1] not in chinese_ender_map.values():
				target += mapped
			elif target[-1] != mapped:
				target = re.sub(r"[。！？，]+$", "", target) + mapped

	# ……。-> ……
	if source.endswith("..."):
		target = re.sub(r'[.…。！？]+(?=[”"’』」》】）〉>\s]*$)', '', target)
		target = re.sub(r'([”"’』」》】）〉>\s]*$)', "……" + r'\1', target)
		return target    
	
	return target

