import subprocess
import pathlib
import csv
import statistics
import os

# === CONFIG ===
NORMALISE_SCRIPT = "***REMOVED***/mono_normalise.py"
TEST_DATA_DIR = pathlib.Path("***REMOVED***/normalisation/testing/unit_test")
OUT_DIR = pathlib.Path("***REMOVED***/normalisation/testing/unit_test_output")
REPORT_FILE = OUT_DIR / "unit_test_report.csv"

# Make sure output dir exists
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_normaliser(lang, infile):
    cmd = [
        "python", NORMALISE_SCRIPT,
        "--input", str(infile),
        "--output_dir", str(OUT_DIR),
        "--l1", lang,
        "--mode", "monolingual"
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        outfile = OUT_DIR / f"{lang}_norm.txt"

        # Try to detect which normaliser file was used from stdout
        norm_file = None
        for line in result.stdout.splitlines():
            if f"Using normaliser for {lang}" in line:
                filepath = line.split(":", 1)[1].strip()
                norm_file = os.path.basename(filepath)

        if outfile.exists():
            return True, None, norm_file
        else:
            return False, f"Expected output file {outfile} not found", norm_file
    except subprocess.CalledProcessError as e:
        return False, e.stderr, None

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

def check_idempotence(lang, outfile):
    IDEM_OUT = OUT_DIR / "idem_output"
    IDEM_OUT.mkdir(exist_ok=True)

    cmd = [
        "python", NORMALISE_SCRIPT,
        "--input", str(outfile),
        "--output_dir", str(IDEM_OUT),
        "--l1", lang,
        "--mode", "monolingual"
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    generated = IDEM_OUT / f"{lang}_norm.txt"
    if not generated.exists():
        return False

    orig = read_lines(outfile)
    tmp = read_lines(generated)
    return orig == tmp

def analyse(lang, infile, outfile):
    inp_lines = read_lines(infile)
    out_lines = read_lines(outfile)

    lines_in = len(inp_lines)
    lines_out = len(out_lines)

    changed = sum(1 for a, b in zip(inp_lines, out_lines) if a != b)
    changed_pct = changed / lines_in * 100 if lines_in > 0 else 0

    ratios = [len(b) / len(a) for a, b in zip(inp_lines, out_lines) if len(a) > 0]
    mean_len_ratio = statistics.mean(ratios) if ratios else 0

    idem = check_idempotence(lang, outfile)

    notes = []
    if lines_in != lines_out:
        notes.append("Line count mismatch")
    if changed_pct == 0:
        notes.append("OK")
    if changed_pct == 100:
        notes.append("All lines changed")
    if mean_len_ratio < 0.7 or mean_len_ratio > 1.3:
        notes.append("Length ratio suspicious")

    return {
        "lang": lang,
        "lines_in": lines_in,
        "lines_out": lines_out,
        "changed_pct": round(changed_pct, 2),
        "mean_len_ratio": round(mean_len_ratio, 2),
        "idempotent": idem,
        "notes": "; ".join(notes) if notes else "REVISE"
    }

def main():
    results = []

    for infile in TEST_DATA_DIR.glob("*.txt"):
        lang = infile.stem  # e.g., "ar" from ar.txt
        outfile = OUT_DIR / f"{lang}_norm.txt"

        ok, err, norm_file = run_normaliser(lang, infile)
        if not ok:
            results.append({
                "lang": lang,
                "lines_in": 0,
                "lines_out": 0,
                "changed_pct": 0,
                "mean_len_ratio": 0,
                "idempotent": False,
                "normaliser_file": norm_file or "N/A",
                "notes": f"FAIL: {err.strip()}"
            })
            continue

        stats = analyse(lang, infile, outfile)
        stats["normaliser_file"] = norm_file or "N/A"
        results.append(stats)

    with open(REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "lang", "lines_in", "lines_out", "changed_pct",
            "mean_len_ratio", "idempotent", "normaliser_file", "notes"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Report written to {REPORT_FILE}")

if __name__ == "__main__":
    main()
