import os
import joblib
import fasttext
from huggingface_hub import hf_hub_download

def load_detector(cache_dir=None):
	# If model.bin was downloaded directly into cache_dir (via --local-dir), use it
	# directly without contacting HuggingFace Hub (compute nodes have no internet).
	if cache_dir and os.path.isfile(os.path.join(cache_dir, "model.bin")):
		model_path = os.path.join(cache_dir, "model.bin")
	else:
		model_path = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model.bin", cache_dir=cache_dir)
	model = fasttext.load_model(model_path)
	return model

def _target_labels(lang):
	if not lang:
		return set()
	langs = lang if isinstance(lang, list) else [lang]
	labels = set()
	for item in langs:
		if not item:
			continue
		labels.add(item if item.startswith("__label__") else f"__label__{item}")
	return labels

def detect_with_glotlid(sentence, lang, detector):
	target_labels = _target_labels(lang)
	if not target_labels:
		return 0
	predicted_languages, raw_probs = detector.predict(sentence, k=-1)
	best = 0
	for label, prob in zip(predicted_languages, raw_probs):
		if label in target_labels:
			best = max(best, prob * 100)
	return best

def score(input_path, output_path, l1, l2, cache_dir=None, langid_l1_targets=None, langid_l2_targets=None):
	glotlid_detector = load_detector(cache_dir=cache_dir)
	l1_targets = langid_l1_targets if langid_l1_targets is not None else l1
	l2_targets = langid_l2_targets if langid_l2_targets is not None else l2

	# Open input TSV and output TSV
	with open(input_path, "r", encoding="utf-8") as infile, \
		 open(output_path, "w", encoding="utf-8") as outfile:

		header = infile.readline().rstrip("\n")
		outfile.write(f"{header}\tl1_prob\tl2_prob\n")

		for line_number, line in enumerate(infile, start=2):
			line = line.rstrip("\n")
			if not line:
				continue
			try:
				l1_sent, l2_sent, *rest = line.split("\t")
			except ValueError:
				print(f"[Warning] Skipping malformed line {line_number}: {line}")
				continue

			l1_prob = detect_with_glotlid(l1_sent, l1_targets, glotlid_detector)
			l2_prob = detect_with_glotlid(l2_sent, l2_targets, glotlid_detector)

			fields = [l1_sent, l2_sent] + rest + [str(l1_prob), str(l2_prob)]
			outfile.write("\t".join(fields) + "\n")
