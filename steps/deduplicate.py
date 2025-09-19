#!/usr/bin/env python3
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import tempfile
import subprocess
from fast_unidecode import unidecode
import xxhash

# Aggressive normalization for deduplication
remove_non_alpha = str.maketrans(
    '', '',
    ''.join([chr(i) for i in range(0x110000) if not chr(i).isalpha() and not chr(i).isspace()])
)

def normalize_for_hash(s: str) -> str:
    s = s.lower()
    s = unidecode(s)
    s = s.translate(remove_non_alpha)
    return " ".join(s.split())

def get_hash(src: str, tgt: str) -> str:
    norm_src = normalize_for_hash(src)
    norm_tgt = normalize_for_hash(tgt)
    return xxhash.xxh64(norm_src + "\t" + norm_tgt).hexdigest()

def get_rank(src: str, tgt: str) -> float:
    text = src + tgt
    if not text:
        return 0.0
    return sum(ord(ch) for ch in text) / len(text)

def deduplicate_tsv(tsv_path: str, out_path: str):
    tmpdir = os.environ.get("TMPDIR") or os.environ.get("TMP") or "/tmp"

    # 1) Stream TSV -> temp file with hash + rank + full line
    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=tmpdir, encoding="utf-8") as tmp:
        tmp_name = tmp.name
        with open(tsv_path, "r", encoding="utf-8") as f_in:
            header = next(f_in)  # preserve header
            for line_number, line in enumerate(f_in, start=2):
                line = line.rstrip("\r\n")
                parts = line.split("\t")
                if len(parts) < 2:
                    print(f"[Warning] skipping malformed line {line_number}: {line}")
                    continue
                s_line, t_line = parts[0], parts[1]
                h = get_hash(s_line, t_line)
                r = get_rank(s_line, t_line)
                tmp.write(f"{h}\t{r:.6f}\t{line}\n")

    # 2) External sort: stable, by hash asc, then rank desc
    _, sorted_name = tempfile.mkstemp(dir=tmpdir)
    os.close(_)  # close fd
    env = dict(os.environ)
    env.setdefault("LC_ALL", "C")
    sort_cmd = [
        "sort",
        "-t", "\t",
        "-k1,1",     # hash
        "-k2,2nr",   # rank descending
        tmp_name,
        "-o", sorted_name
    ]
    subprocess.run(sort_cmd, check=True, env=env)

    # 3) Stream sorted file, keep first occurrence of each hash
    with open(sorted_name, "r", encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        fout.write(header)  # preserve original header
        last_hash = None
        for line in fin:
            parts = line.rstrip("\n").split("\t", 3)
            if len(parts) < 4:
                continue
            h, _rank, s_line, t_line = parts
            if h != last_hash:
                fout.write(f"{s_line}\t{t_line}\n")
                last_hash = h

    # 4) Cleanup temp files
    for f in [tmp_name, sorted_name]:
        try:
            os.remove(f)
        except OSError:
            pass
