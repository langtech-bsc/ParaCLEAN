# pipeline.py
import argparse
import json
import os
from steps import input_formats, embeddings, langid, filtering, deduplicate, normalisation

def run_pipeline_from_config(config):
	"""
	Run pipeline using a config dictionary.
	"""
	inputs = config.get("inputs")
	if inputs:
		out_dir=config.get("output")
		if out_dir is None:
			raise ValueError("Config must include an 'output' directory")
		os.makedirs(out_dir, exist_ok=True)
		results = {}
		for inp in inputs:
			name = inp["name"]
			print(f"[pipeline] Processing input set: {name}")
			result = run_pipeline(
				input_path=inp["paths"],
				output_path = os.path.join(out_dir, name),
				steps=config.get("steps"),
				l1=config.get("l1"),
				l2=config.get("l2"),
				format=inp.get("type", config.get("format", "plain_text")),
				alignment=config.get("alignment_score"),
				langid_l1=config.get("langid_l1_prob"),
				langid_l2=config.get("langid_l2_prob"),
				model=config.get("model", "labse"),
				model_path=config.get("model_path")
			)
			results[name] = result
		return results
	else:
		# fallback to single-input config
		return run_pipeline(
			input_path=config.get("input"),
			output_path=config.get("output"),
			l1=config.get("l1"),
			l2=config.get("l2"),
			format=config.get("format", "plain_text"),
			alignment=config.get("alignment_score"),
			langid_l1=config.get("langid_l1_prob"),
			langid_l2=config.get("langid_l2_prob"),
			model=config.get("model", "labse"),
			model_path=config.get("model_path")
		)

# def load_embedding_model(name, model_path=None):
# 	"""
# 	Factory for loading embedding models.
# 	Extend this as new models are supported.
# 	"""
# 	if name == "labse":
# 		print("[pipeline] Loading LaBSE model...")
# 		from sentence_transformers import SentenceTransformer
# 		# If a local path is provided, use it
# 		if model_path is not None:
# 			return SentenceTransformer(model_path)
# 		else:
# 			# Otherwise, use Hugging Face model name to auto-download
# 			hf_model_name = "sentence-transformers/LaBSE"
# 			cache_dir = os.path.expanduser("~/.cache/my_pipeline_models")
# 			return SentenceTransformer(hf_model_name, cache_folder=cache_dir)

# 	elif name == "comet":
# 		# placeholder, you can add COMET model loading here
# 		raise NotImplementedError("COMET embeddings not yet supported")


# 	elif name == "sonar":
# 		try:
# 			import torch
# 			from sonar.inference_pipelines.text import TextToEmbeddingModelPipeline
# 		except ImportError:
# 			raise ImportError(
# 				"SONAR requested but not installed. "
# 				"Install with `pip install sonar-space` and the correct fairseq2 build."
# 			)

# 		class SonarAdapter:
# 			def __init__(self, device=None, dtype=None):
# 				self.model = TextToEmbeddingModelPipeline(
# 					encoder="text_sonar_basic_encoder",
# 					tokenizer="text_sonar_basic_encoder",
# 					device=device or torch.device("cpu"),
# 					dtype=dtype or torch.float32,
# 				)

# 			def encode(self, sentences, lang="en"):
# 				flores_code = get_flores_code(lang)
# 				embs = self.model.predict(sentences, source_lang=flores_code)
# 				return embs.cpu().numpy()  # match SentenceTransformer return type

# 		print("[pipeline] Loading SONAR text embedding model...")
# 		return SonarAdapter()

# 	else:
# 		raise ValueError(f"Unsupported embedding model: {name}")

# 	else:
# 		raise ValueError(f"Unsupported embedding model: {name}")


def run_pipeline(
	input_path, 
	output_path, 
	steps, 
	l1, 
	l2, 
	format, 
	filter_config=None,
	model="labse",
	model_path=None,
	alignment=None,
	langid_l1=None,
	langid_l2=None
	):
	"""
	Run the full pipeline or selected steps.
	"""
	data = None

	# Step: input reading
	if "input" in steps:
		print(f"[pipeline] Reading and formatting input: {input_path}")
		
		# Write reformatted TSV to a temporary file
		formatted_path = output_path + ".formatted.tsv"
		
		# Convert input format -> TSV
		input_formats.run(
			input_files=input_path,
			l1=l1,
			l2=l2,
			input_format=format,
			output=formatted_path
		)
		
		# Instead of loading into memory, just pass the path to downstream steps
		data_path = formatted_path
		print(f"[pipeline] Reformatted TSV written to: {formatted_path}")

	if "embeddings" in steps:
		current_path= output_path + ".formatted.tsv"
		embedding_model = embeddings.load_embedding_model(model, model_path=model_path)
		embeddings_output = output_path + ".embeddings.tsv"
		print(f"[pipeline] Computing embeddings with {model}")
		embeddings.add_embeddings(current_path, embeddings_output, model=embedding_model,
							  l1=l1, l2=l2)
		

	# Step: language ID
	if "langid" in steps:
		current_path = output_path + ".embeddings.tsv"
		langid_output = output_path + ".langid.tsv"
		print(f"[pipeline] Running language ID")
		data = langid.score(current_path, langid_output, l1, l2)

	if "dedup" in steps:
		current_path = output_path + ".langid.tsv"
		deduped_path = output_path + ".deduped.tsv"
		data = deduplicate.deduplicate_tsv(current_path, deduped_path)
		print(f"[pipeline] Deduplicated TSV written to: {deduped_path}")

	if "filter" in steps:
		print(f"[pipeline] Applying filters")
		current_path = output_path + ".deduped.tsv"
		filtered_path = output_path + ".filtered.tsv"
		filtering.apply_filters(current_path, filtered_path, alignment, langid_l1, langid_l2)
		print(f"[pipeline] Filtered TSV written to: {filtered_path}")


	# Step: normalization
	if "normalise" in steps:
		current_path = output_path + ".filtered.tsv"
		output_path = output_path + ".normalised.tsv"
		print(f"[pipeline] Normalising")
		data = normalisation.apply_normalisation(current_path, output_path, l1, l2)

	return data


def main():
	parser = argparse.ArgumentParser(description="Run the data cleaning pipeline.")
	parser.add_argument("--config", type=str, help="Path to JSON config file with pipeline arguments")
	args = parser.parse_args()

	if args.config:
		with open(args.config, "r", encoding="utf-8") as f:
			config = json.load(f)
		run_pipeline_from_config(config)
	else:
		parser.error("You must provide a --config JSON file")

if __name__ == "__main__":
	main()
