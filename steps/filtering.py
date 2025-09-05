#!/usr/bin/env python3
import csv
import json

def load_filter_config(config_path):
    """Load JSON config for filtering thresholds."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def apply_filters(input_path, output_path, config):
    """
    Stream TSV file, apply filters, and write passing rows to output.
    Only considers first two columns for language/text filters; can be extended.
    """
    alignment_thresh = config.get("alignment_score", 0.0)
    langid_l1_thresh = config.get("langid_l1_prob", 0.0)
    langid_l2_thresh = config.get("langid_l2_prob", 0.0)
    max_length_diff = config.get("max_length_diff", None)

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        reader = csv.reader(infile, delimiter="\t", quoting=csv.QUOTE_NONE)
        writer = csv.writer(outfile, delimiter="\t", quoting=csv.QUOTE_MINIMAL)

        # Write header
        header = next(reader)

        for line_number, row in enumerate(reader, start=2):
            try:
                l1_sent, l2_sent, *rest = row
            except ValueError:
                print(f"[Warning] Skipping malformed line {line_number}: {row}")
                continue

            # 1) Alignment score filter
            if alignment_thresh > 0.0:
                # assume the alignment score is the last column if present
                align_score = float(rest[0]) if rest else 1.0
                if align_score < alignment_thresh:
                    continue

            # 2) Language ID filter
            if langid_l1_thresh > 0.0:
                l1_prob = float(rest[1]) if len(rest) > 1 else 1.0
                if l1_prob < langid_l1_thresh:
                    continue

            if langid_l2_thresh > 0.0:
                l2_prob = float(rest[2]) if len(rest) > 2 else 1.0
                if l2_prob < langid_l2_thresh:
                    continue

            # Passed all filters, write row as-is
            writer.writerow([l1_sent, l2_sent])
