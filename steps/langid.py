import joblib
import fasttext
from lingua import Language, LanguageDetectorBuilder
from languages import language_identification, idioma_languages

idioma_default = ['arn', 'oc', 'gl']

def load_detectors():
	"""
	Load all detectors once to avoid reloading for each line.
	"""
	idioma_detector = joblib.load("***REMOVED***/idioma_cognitor/model.pkl")
	lingua_options = list(language_identification.values())
	lingua_detector = LanguageDetectorBuilder.from_languages(*lingua_options).build()
	fasttext_detector = fasttext.load_model("***REMOVED***/fast_text/model.bin")
	
	return idioma_detector, lingua_detector, fasttext_detector

def detect_with_idioma(sentence, lang, idioma_detector):
	idioma_reversed = {v: k for k, v in idioma_languages.items()}
	index_lang = int(idioma_reversed[lang]) - 1
	probabilities = idioma_detector.predict_proba([sentence])
	return float(probabilities[0][index_lang])

def detect_with_lingua(sentence, lang, lingua_detector):
	lang_prob = lingua_detector.compute_language_confidence(sentence, language_identification[lang])
	return float(lang_prob)

def detect_with_fasttext(sentence, lang, fasttext_detector):
	predictions = fasttext_detector.predict(sentence, k=20)
	predicted_languages = predictions[0] 
	probabilities = predictions[1]
	target_label = f"__label__{lang}"
	for label, prob in zip(predicted_languages, probabilities):
		if label == target_label:
			return float(prob)
	return 0.5  # default if not found

def score(input_path, output_path, l1, l2):
	idioma_detector, lingua_detector, fasttext_detector = load_detectors()

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

			# Pick correct detector for each language
			if l1 in idioma_default:
				l1_prob = detect_with_idioma(l1_sent, l1, idioma_detector)
			elif l1 in language_identification:
				l1_prob = detect_with_lingua(l1_sent, l1, lingua_detector)
			else:
				l1_prob = detect_with_fasttext(l1_sent, l1, fasttext_detector)

			if l2 in idioma_default:
				l2_prob = detect_with_idioma(l2_sent, l2, idioma_detector)
			elif l2 in language_identification:
				l2_prob = detect_with_lingua(l2_sent, l2, lingua_detector)
			else:
				l2_prob = detect_with_fasttext(l2_sent, l2, fasttext_detector)
				
			fields = [l1_sent, l2_sent] + rest + [str(l1_prob), str(l2_prob)]
			outfile.write("\t".join(fields) + "\n")
