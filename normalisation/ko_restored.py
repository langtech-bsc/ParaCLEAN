import re
import unicodedata
from tqdm import tqdm


#  In modern South Korean writing, the standard is to use half-width (ASCII) punctuation 

def normalise(text: str, source: str = "") -> str:
    # Unicode compatibility normalization
    text = unicodedata.normalize("NFKC", text)

    # Remove leading/trailing whitespace and full-width spaces
    text = text.strip().replace("\u3000", "")

    # Remove unnecessary spaces within text
    text = re.sub(r"[\u3000\s\t]+", " ", text)
    
    # convert East Asian / full-width → ASCII
    text = re.sub(r'。', '.', text)
    text = re.sub(r'．', '.', text)
    text = re.sub(r'、', ',', text)
    text = re.sub(r'，', ',', text)
    text = re.sub(r'：', ':', text)
    text = re.sub(r'；', ';', text)
    text = re.sub(r'？', '?', text)
    text = re.sub(r'！', '!', text)

    # parentheses
    text = re.sub(r'（', '(', text)
    text = re.sub(r'）', ')', text)

    # Trim spaces just inside parentheses: "( 텍스트 )" → "(텍스트)"
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    
    # Remove space after closing parenthesis if followed by a Korean particle (e.g., 이/가/은/는/을/를)
    text = re.sub(r"\)\s+(?=(?:이|가|은|는|을|를|도|만|에서|으로|와|과|에게|께서))", ")", text)

    # quotes
    text = re.sub(r'[「『]', '"', text)
    text = re.sub(r'[」』]', '"', text)
    text = re.sub(r'[“”]', '"', text)
    text = re.sub(r'[‘’]', "'", text)
    text = re.sub(r"''([^']*?)''", r'"\1"', text)

    # ellipsis
    text = re.sub(r"\.{3,}", "…", text)
    text = re.sub(r"…{2,}", "…", text)    
    text = re.sub(r'(…)(?=[가-힣])', r'\1 ', text)

    # others
    text = re.sub(r'〜', '~', text)
    text = re.sub(r'～', '~', text)
    text = re.sub(r"(\d)\s+%", r"\1%", text) # remove the extra spaces between the digit and %
    text = re.sub(r'(\d+)\s+(분|월|명|개|년|도|m|kg|%)', r'\1\2', text)
    text = re.sub(r'£\s*(\d+[a-zA-Z]*)', r'£\1', text)
    
    # add missing space after the period
    text = re.sub(r"(?<!\.\.)\.(?=[가-힣])", ". ", text)
    # add missing space after the comma
    text = re.sub(r",(?=[가-힣])", ", ", text)
    
    # Add space after closing punctuation if followed by Korean character
    text = re.sub(r"([!?])(?=[가-힣])", r"\1 ", text)
    # Remove space before punctuation
    text = re.sub(r"\s+([.,!?])", r"\1", text)    
        
    # Optionally fix final punctuation to match source sentence
    if source:
        text = match_sentence_ender(source, text)

    return text


def match_sentence_ender(source: str, target: str) -> str:
    # Sentence-ending punctuation across languages
    source_enders = {'.', '!', '?', '。', '！', '？', '؟', '․', '‽', '⸮', '؛', '。', '！', '？', '।', '۔'}

    # Mapping source punctuation to Korean equivalents 
    ko_ender_map = {
        '.': '.',
        '․': '.',
        '!': '!',
        '！': '!',
        '?': '?',
        '？': '?',
        '؟': '?',
        '‽': '?',
        '⸮': '?',
        '؛': '.', # Semicolon → sentence end (neutral handling)
        '۔': '.',  # Arabic/Urdu full stop
        '।': '.',  # Devanagari danda
        '。': '.',  # Chinese period -> .
    }

    source = source.strip()
    target = target.strip()

    source_punct = source[-1] if source and source[-1] in source_enders else None

    if source_punct:
        mapped = ko_ender_map.get(source_punct)
        if mapped:
            if not target or target[-1] not in ko_ender_map.values():
                target += mapped
            elif target[-1] != mapped:
                target = re.sub(r"[…\.!\?]+$", "", target) + mapped

    return target

def process_file_with_source(source_path: str, target_path: str, output_path: str):
    with open(source_path, 'r', encoding='utf-8') as src_file, \
         open(target_path, 'r', encoding='utf-8') as tgt_file, \
         open(output_path, 'w', encoding='utf-8') as out_file:
        for src_line, tgt_line in tqdm(zip(src_file, tgt_file), desc="Normalising"):
        #for src_line, tgt_line in zip(src_file, tgt_file):
            src_line = src_line.strip()
            tgt_line = tgt_line.strip()

            if not tgt_line:
                out_file.write("\n")
                continue

            normalised = normalise(tgt_line, source=src_line)
            out_file.write(normalised + "\n")
            
if __name__ == "__main__":
    source_file = "/gpfs/projects/bsc88/data/04-mt-samplings/es-ko/es_EN-ko_30M.es"
    target_file = "/gpfs/projects/bsc88/data/04-mt-samplings/es-ko/es_EN-ko_30M.ko"
    output_file = "/gpfs/projects/bsc88/data/04-mt-samplings/es-ko/es_EN-ko_30M.ko_normalised"

    process_file_with_source(source_file, target_file, output_file)