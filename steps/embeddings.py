
# steps/embeddings.py
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import csv
from .mappings import get_flores_code

def load_embedding_model(name, model_path=None):
	"""
	Factory for loading embedding models.
	Extend this as new models are supported.
	"""
	if name == "labse":
		print("[embeddings] Loading LaBSE model...")
		if model_path is not None:
			return SentenceTransformer(model_path)
		else:
			hf_model_name = "sentence-transformers/LaBSE"
			cache_dir = os.path.expanduser("~/.cache/my_pipeline_models")
			return SentenceTransformer(hf_model_name, cache_folder=cache_dir)

	elif name == "comet":
		raise NotImplementedError("COMET embeddings not yet supported")

	elif name == "sonar":
		try:
			import torch
			from sonar.inference_pipelines.text import TextToEmbeddingModelPipeline
			from .mappings import get_flores_code
		except ImportError:
			raise ImportError(
				"SONAR requested but not installed. "
				"Install with `pip install sonar-space` and the correct fairseq2 build."
			)

		class SonarAdapter:
			def __init__(self, device=None, dtype=None):
				self.model = TextToEmbeddingModelPipeline(
					encoder="text_sonar_basic_encoder",
					tokenizer="text_sonar_basic_encoder",
					device=device or torch.device("cpu"),
					dtype=dtype or torch.float32,
				)

			def encode(self, sentences, lang="en"):
				flores_code = get_flores_code(lang)
				embs = self.model.predict(sentences, source_lang=flores_code)
				return embs.cpu().numpy()

		print("[embeddings] Loading SONAR text embedding model...")
		return SonarAdapter()

	else:
		raise ValueError(f"Unsupported embedding model: {name}")


def add_embeddings(tsv_path, output_path, model, l1="en", l2="en"):
	"""
	Read a TSV file line by line, compute embeddings, and write out to a new TSV
	with cosine similarity.
	"""
	from sentence_transformers import SentenceTransformer

	with open(tsv_path, "r", encoding="utf-8") as infile, \
		 open(output_path, "w", encoding="utf-8") as outfile:

		header = infile.readline().rstrip("\n")
		outfile.write(f"{header}\tcosine_similarity\n")

		for line_number, line in enumerate(infile, start=2):
			line = line.rstrip("\n")
			if not line:
				continue
			try:
				l1_sent, l2_sent = line.split("\t")
			except ValueError:
				print(f"[Warning] Skipping malformed line {line_number}: {line}")
				continue

			# If it's SONAR, pass langs explicitly
			if hasattr(model, "encode") and "lang" in model.encode.__code__.co_varnames:
				emb1 = model.encode([l1_sent], lang=l1)[0]
				emb2 = model.encode([l2_sent], lang=l2)[0]
			else:
				# e.g. LaBSE — just encode directly
				emb1, emb2 = model.encode([l1_sent, l2_sent])

			cos_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
			outfile.write(f"{l1_sent}\t{l2_sent}\t{cos_sim}\n")
