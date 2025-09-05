# pipeline.py
import argparse
from steps import input_formats, embeddings, langid, filtering, deduplication

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

def run_pipeline(input_path, output_path, steps, l1, l2, format, model="labse"):
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
		deduplicate_tsv(current_path, deduped_path)
		current_path = deduped_path
		print(f"[pipeline] Deduplicated TSV written to: {deduped_path}")


	# Step: filtering
	if "filter" in steps:
		print(f"[pipeline] Filtering")
		data = filtering.apply_filters(data)

	# Step: normalization
	if "normalize" in steps:
		print(f"[pipeline] Normalizing")
		data = normalization.apply_normalization(data, l1, l2)

	# Step: output writing
	if "output" in steps:
		print(f"[pipeline] Writing output to {output_path}")
		input_formats.save(data, output_path)

	return data


def main():
	parser = argparse.ArgumentParser(description="Run the data cleaning pipeline.")
	parser.add_argument("--input", help="Path to input file", nargs = '+')
	parser.add_argument("--output", required=True, help="Path to save results")
	parser.add_argument("--steps", default="input,embeddings,langid,filter,dedup,normalize,output",
						help="Comma-separated list of steps to run")
	parser.add_argument("--l1", required=True, help="Source language code")
	parser.add_argument("--l2", required=True, help="Target language code")
	parser.add_argument("--format",default="tsv")
	parser.add_argument("--model", default="labse", help="Embedding model to use (labse, comet, sonar...)")

	args = parser.parse_args()
	steps = [s.strip() for s in args.steps.split(",")]

	run_pipeline(args.input, args.output, steps, args.l1, args.l2, args.format, model=args.model)


if __name__ == "__main__":
	main()
