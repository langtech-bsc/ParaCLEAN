import re
import unicodedata

def normalise(text: str, source: str = "") -> str:
    # Unicode compatibility normalization
    text = unicodedata.normalize("NFKC", text)

    # Remove leading/trailing whitespace and full-width spaces
    text = text.strip().replace("\u3000", "")

    # Remove unnecessary ASCII spaces within text (not between Chinese chars)
    text = re.sub(r"[ \t]+", "", text)

    # Replace half-width punctuation with full-width Chinese equivalents
    # text = text.replace(",", "，").replace(".", "。").replace(":", "：").replace(";", "；")
    # text = text.replace("?", "？").replace("!", "！")
    text = text.replace(";", "；")
    text = text.replace("?", "？").replace("!", "！")
    # Replace ellipsis
    # text = text.replace("...", "……")
    # text = text.replace("…", "……")
    text = re.sub(r'(?<!…)\…(?!…)|\.{6}|(?<!\.{3})\.{3}(?!\.{3})|······', '……', text)
    # Replace . after Chinese characters with the Chinese period
    text = re.sub(r'(?<=[\u4e00-\u9fff])\.', '。', text)
    # Further replace periods (.) only if they are not part of initials, numbers, or technical terms like U.S. 3.14
    # Use negative lookbehind and lookahead to exclude such cases
    text = re.sub(r'(?<![A-Za-z0-9])\.(?![A-Za-z0-9])', '。', text)
    # Replace commas not between digits, also cases like "他们称之为X17,因为他们计算出其质量为17兆电子伏。"    
    text = re.sub(r'(?<!\d),|,(?!\d)', '，', text)
    # Replace colons (:) only if they are not part of time notations or ratios
    # This uses a negative lookbehind for digits and a negative lookahead for digits, ensuring colons used in time or ratio contexts are not replaced
    text = re.sub(r'(?<!\d):(?!\d)', '：', text)
    
    

    # Replace ASCII quotation marks with Chinese quotes
    text = text.replace('"', '”')  # default to closing if unsure of context
    text = text.replace("'", "’")

    # Replace brackets
    text = text.replace("(", "（").replace(")", "）")

    # Replace 「 with Chinese opening quote and 」 with Chinese closing quote
    text = text.replace('「', '“')
    text = text.replace('」', '”') 
    
    text = text.replace('『', '“')
    text = text.replace('』', '”')



    # Replace multiple consecutive dashes with a single em dash
    text = re.sub(r'-{2,}', '——', text)  
    # Replace extra single dashes with Chinese equivalents
    text = text.replace("–", "——").replace("—", "——")

    # Correct the use of a slight-pause mark used to set off items in a series
    text = re.sub(r'(?<=[\u4e00-\u9fff])丶(?=[\u4e00-\u9fff])', '、', text)

    # correct the · between names
    text = re.sub(r'(?<=[\u4e00-\u9fff])•(?=[\u4e00-\u9fff])', '·', text)

    # Remove control characters and invalid Unicode ranges
    text = re.sub(r"[^\u4E00-\u9FFF\u3000-\u303F\uFF00-\uFFEF\u4DC0-\u4DFF\u2000-\u206F\u2E80-\u2EFF\u3400-\u4DBF\w\s]", "", text)

    # Optionally fix final punctuation to match source sentence
    if source:
        text = match_sentence_ender(source, text)

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
        '।': '。'   # Devanagari danda
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
                target = re.sub(r"[。！？]+$", "", target) + mapped

    return target