import joblib
import fasttext
from huggingface_hub import hf_hub_download

def load_detector():
	model_path = hf_hub_download(repo_id="cis-lmu/glotlid", filename="model.bin", cache_dir=None)
	model = fasttext.load_model(model_path)
	return model

def detect_with_glotlid(sentence, lang, detector):
	predictions = detector.predict(sentence)
	predicted_languages = predictions[0]
	raw_probs = predictions[1]
	total = sum(raw_probs)
	norm_probs = [float(p / total * 100) for p in raw_probs]
	target_label = f"__label__{lang}"
	for label, prob in zip(predicted_languages, norm_probs):
		if label == target_label:
			return prob
	return 0  # default if not found

def score(input_path, output_path, l1, l2):
	glotlid_detector = load_detector()

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

			l1_prob = detect_with_glotlid(l1_sent, l1, glotlid_detector)
			l2_prob = detect_with_glotlid(l2_sent, l2, glotlid_detector)

			fields = [l1_sent, l2_sent] + rest + [str(l1_prob), str(l2_prob)]
			outfile.write("\t".join(fields) + "\n")

