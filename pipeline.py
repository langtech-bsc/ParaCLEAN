# pipeline.py
import argparse
from steps import input_formats, embeddings, langid, filtering, deduplicate, normalisation

def load_embedding_model(name):
	"""
	Factory for loading embedding models.
	Extend this as new models are supported.
	"""
	if name == "labse":
		from sentence_transformers import SentenceTransformer
		print("[pipeline] Loading LaBSE model...")
		return SentenceTransformer("***REMOVED***/labse_model")

	elif name == "comet":
		# placeholder, you can add COMET model loading here
		raise NotImplementedError("COMET embeddings not yet supported")

	elif name == "sonar":
		# placeholder
		raise NotImplementedError("SONAR embeddings not yet supported")

	else:
		raise ValueError(f"Unsupported embedding model: {name}")

def run_pipeline(input_path, output_path, steps, l1, l2, format, filter_config=None, model="labse"):
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
		embedding_model = load_embedding_model(model)
		embeddings_output = output_path + ".embeddings.tsv"
		print(f"[pipeline] Computing embeddings with {model}")
		embeddings.add_embeddings(current_path, embeddings_output, model=embedding_model)
		

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
		filter_config = filtering.load_filter_config(filter_config)
		current_path = output_path + ".deduped.tsv"
		filtered_path = output_path + ".filtered.tsv"
		filtering.apply_filters(current_path, filtered_path, filter_config)
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
	parser.add_argument("--input", help="Path to input file", nargs = '+')
	parser.add_argument("--output", required=True, help="Path to save results")
	parser.add_argument("--steps", default="input,embeddings,langid,filter,dedup,normalise,output",
						help="Comma-separated list of steps to run")
	parser.add_argument("--l1", required=True, help="Source language code")
	parser.add_argument("--l2", required=True, help="Target language code")
	parser.add_argument("--format",default="tsv")
	parser.add_argument("--model", default="labse", help="Embedding model to use (labse, comet, sonar...)")
	parser.add_argument("--filter_config", type=str, default="filter_config.json", help="Path to JSON file specifying filtering thresholds (alignment, langid, etc.)"
)

	args = parser.parse_args()
	steps = [s.strip() for s in args.steps.split(",")]

	run_pipeline(
		args.input, 
		args.output, 
		steps, 
		args.l1, 
		args.l2, 
		args.format, 
		args.filter_config, 
		model=args.model)


if __name__ == "__main__":
	main()
