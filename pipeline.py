# pipeline.py
import argparse
import yaml
import os
import subprocess
from steps import input_formats, embeddings, langid, filtering, deduplicate, normalisation, bifixer

MERGED_STEPS = {"dedup", "filter", "normalise", "bifixer"}
PER_CORPUS_STEPS = {"input", "embeddings", "langid"}

def ensure_dir(path):
	os.makedirs(path, exist_ok=True)

def run_pipeline_from_config(config):
	"""
	Entry point for running the pipeline from a config dict.
	Handles both single-corpus and multi-corpus modes.
	"""
	if not config.get("inputs"):
		return run_single_corpus(config)

	return run_multi_corpus(config)


def run_single_corpus(config):
	ensure_dir(os.path.dirname(config["output"]))
	return run_pipeline(
		input_path=config.get("input"),
		output_path=config["output"],
		steps=config.get("steps", []),
		l1=config.get("l1"),
		l2=config.get("l2"),
		format=config.get("format", "plain_text"),
		alignment=config.get("alignment_score"),
		langid_l1=config.get("langid_l1_prob"),
		langid_l2=config.get("langid_l2_prob"),
		model=config.get("model", "labse"),
		model_path=config.get("model_path"),
		start_from=config.get("start_from"),
		bifixer_flags=config.get("bifixer_flags", None)
	)


def run_multi_corpus(config):
	out_dir = config["output"]
	ensure_dir(out_dir)

	merged_steps = [s for s in config.get("steps", []) if s in MERGED_STEPS]
	intermediate_paths = []

	for inp in config["inputs"]:
		result_path = run_single_input(inp, config, out_dir)
		if result_path:
			intermediate_paths.append(result_path)

	if not merged_steps:
		return intermediate_paths

	merged_path = merge_inputs(intermediate_paths, out_dir)
	return run_pipeline(
		input_path=merged_path,
		output_path=os.path.join(out_dir, "merged"),
		steps=merged_steps,
		l1=config.get("l1"),
		l2=config.get("l2"),
		format="tsv",
		alignment=config.get("alignment_score"),
		langid_l1=config.get("langid_l1_prob"),
		langid_l2=config.get("langid_l2_prob"),
		model=config.get("model", "labse"),
		model_path=config.get("model_path"),
		bifixer_flags=config.get("bifixer_flags", None)
	)


def run_single_input(inp, config, out_dir):
	"""Run per-corpus steps for a single input definition."""
	name = inp["name"]
	base_out = os.path.join(out_dir, name)
	steps_to_run = [s for s in inp.get("steps", []) if s in PER_CORPUS_STEPS]

	if inp.get("start_from") and not steps_to_run:
		return inp["start_from"]

	print(f"[pipeline] Processing corpus: {name}")
	return run_pipeline(
		input_path=None if inp.get("start_from") else inp.get("paths"),
		output_path=base_out,
		steps=steps_to_run,
		l1=config.get("l1"),
		l2=config.get("l2"),
		format=inp.get("type", config.get("format", "plain_text")),
		alignment=config.get("alignment_score"),
		langid_l1=config.get("langid_l1_prob"),
		langid_l2=config.get("langid_l2_prob"),
		model=config.get("model", "labse"),
		model_path=config.get("model_path"),
		start_from=inp.get("start_from"),
		bifixer_flags=config.get("bifixer_flags", None)
	)


def merge_inputs(intermediate_paths, out_dir):
	"""Concatenate TSV files into one merged file (with header)."""
	merged_path = os.path.join(out_dir, "merged.langid.tsv")
	with open(merged_path, "w", encoding="utf8") as fout:
		header_written = False
		for path in intermediate_paths:
			with open(path, "r", encoding="utf8") as fin:
				header = next(fin)
				if not header_written:
					fout.write(header)
					header_written = True
				fout.writelines(fin)
	print(f"[pipeline] Merged TSV written to {merged_path}")
	return merged_path


def run_pipeline(input_path, output_path, steps, l1, l2, format,
				 filter_config=None, model="labse", model_path=None,
				 alignment=None, langid_l1=None, langid_l2=None,
				 start_from=None, bifixer_flags=None):
	"""
	Run the full pipeline or selected steps.
	bifixer_flags: optional list of strings with flags for Bifixer step
	"""
	current = start_from
	step_fns = {
		"input": lambda p: input_formats.run(
			input_files=input_path, l1=l1, l2=l2, input_format=format,
			output=p + ".formatted.tsv"),
		"embeddings": lambda p: embeddings.add_embeddings(
			current, p + ".embeddings.tsv",
			model=embeddings.load_embedding_model(model, model_path),
			l1=l1, l2=l2),
		"langid": lambda p: langid.score(current, p + ".langid.tsv", l1, l2),
		"filter": lambda p: filtering.apply_filters(
			current, p + ".filtered.tsv", alignment, langid_l1, langid_l2),
		"dedup": lambda p: deduplicate.deduplicate_tsv(current, p + ".deduped.tsv"),
		"normalise": lambda p: normalisation.apply_normalisation(
			current, p + ".normalised.tsv", l1, l2),
		"bifixer": lambda p: bifixer.run(current, p + ".bifixer.tsv",l1, l2, flags=bifixer_flags),
	}

	for step in steps:
		if current is None and step == "input":
			current = input_path
		if current is None and step == "filter":
			current = input_path
		if current is None:
			raise ValueError(f"No TSV available before step '{step}'")
		print(f"[pipeline] Running step: {step}")
		out_path = output_path  # used as prefix
		step_fns[step](out_path)
		suffix = {
			"input": ".formatted.tsv",
			"embeddings": ".embeddings.tsv",
			"langid": ".langid.tsv",
			"filter": ".filtered.tsv",
			"dedup": ".deduped.tsv",
			"normalise": ".normalised.tsv",
			"bifixer": ".bifixer.tsv"
		}[step]
		current = out_path + suffix

	return current


def main():
	parser = argparse.ArgumentParser(description="Run the data cleaning pipeline.")
	parser.add_argument("--config", type=str, required=True,
						help="Path to YAML config file")
	args = parser.parse_args()

	with open(args.config, "r", encoding="utf-8") as f:
		config = yaml.safe_load(f)
	run_pipeline_from_config(config)


if __name__ == "__main__":
	main()
