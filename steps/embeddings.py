# import sys
# from sentence_transformers import SentenceTransformer
# import numpy as np
# import joblib
# from numpy.linalg import norm
# import json
# import os
# import fasttext
# from lingua import Language, LanguageDetectorBuilder
# from languages import language_identification, idioma_languages
# from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
# from sklearn.metrics.pairwise import cosine_similarity
# import input_formats

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# idioma_default = ['arn', 'oc', 'gl']

# def add_base_arguments_to_parser(parser):
#     parser.add_argument(
#         '--metadata',
#         type=str,
#         required=True,
#         help='Path to the metadata file.'
#     )
#     parser.add_argument(
#         '--input_format',
#         type=str,
#         default="tsv",
#         help='Input format to be used.'
#     )
#     parser.add_argument(
#         '--split',
#         type=int,
#         default=0,
#         help='Array index for Slurm array job.'
#     )
#     parser.add_argument(
#         '--l1',
#         type=str,
#         required=True,
#         help='Input format to be used.'
#     )
#     parser.add_argument(
#         '--l2',
#         type=str,
#         required=True,
#         help='Input format to be used.'
#     )

# def detect_with_idioma(sentence, lang):
#     idioma_reversed = {v: k for k, v in idioma_languages.items()}
#     index_lang = int(idioma_reversed[lang]) - 1
#     probabilities = idioma_detector.predict_proba([sentence])
#     prob_lang = str(probabilities[0][index_lang])
#     return prob_lang



# def detect_with_lingua(sentence, language):
#     lang_prob = lingua_detector.compute_language_confidence(sentence, language_identification[language])
#     return lang_prob

# def detect_with_fasttext(sentence, language):
#     predictions=fasttext_detector.predict(sentence, k=20)
#     predicted_languages = predictions[0] 
#     probabilities = predictions[1]  

#     target_language_code = f"__label__{language}"
#     target_probability = 0.5

#     # Check if the target language is in the predictions
#     for lang, prob in zip(predicted_languages, probabilities):
#         if lang == target_language_code:  # Check for the specific language
#             target_probability = prob
#             break

#     return target_probability


# if __name__ == "__main__":

#     # parse arguments
#     description = """SCORING"""  # TODO: improve description
#     parser = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)
#     add_base_arguments_to_parser(parser)
#     args = parser.parse_args()

#     # Creating instance based on input format
#     instance = eval("input_formats." + args.input_format + "(args)")
#     instance.get_paths()

#     print('loading model')
#     os.environ["TRANSFORMERS_OFFLINE"] = "1"
#     model=SentenceTransformer('***REMOVED***/labse_model')
#     print('model loaded')

#     idioma_detector = joblib.load("***REMOVED***/idioma_cognitor/model.pkl")
#     lingua_options = list(language_identification.values())
#     lingua_detector = LanguageDetectorBuilder.from_languages(*lingua_options).build()
#     fasttext_detector = fasttext.load_model("***REMOVED***/fast_text/model.bin")

#     output_path = '{}.{:02d}.tsv'.format(instance.paths["output"], args.split)

#     with open(output_path, 'w') as output:

#         l1 = args.l1
#         l2 = args.l2

#         if l1 in idioma_default:
#             compute_confidence_l1=detect_with_idioma
#             print(l1 + " is an idioma cognitor language")
#         elif l1 in list(language_identification.keys()): 
#             compute_confidence_l1=detect_with_lingua
#             print(l1 + " is a lingua language")
#         else: 
#             compute_confidence_l1=detect_with_fasttext
#             print(l1 + " will try to score with fasttext, if not supported will default to 0.5")

#         if l2 in idioma_default:
#             compute_confidence_l2=detect_with_idioma
#             print(l2 + " is an idioma cognitor language")
#         elif l2 in list(language_identification.keys()): 
#             compute_confidence_l2=detect_with_lingua
#             print(l2 + " is an lingua language")
#         else: 
#             compute_confidence_l2=detect_with_fasttext
#             print(l2 + " will try to score with fasttext, if not supported will default to 0.5")

#         print('{}'.format(l1), '{}'.format(l2), l1 + '_prob', l2 + '_prob', 'alignment', sep='\t', file=output)

#         for l1_sent, l2_sent in instance.read_split(args.split):
#             if l1_sent == '' or l2_sent == '':
#                 continue
#             sentence_pair = [l1_sent, l2_sent]
#             embeddings = model.encode(sentence_pair)
#             cosine_similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
#             try:
#                 confidence_value_l1 = compute_confidence_l1(l1_sent,l1)
#             except NameError:
#                 print(f"Error in compute_confidence_l1: {e}")
#                 confidence_value_l1 = 0.5
#             try:
#                 confidence_value_l2 = compute_confidence_l2(l2_sent,l2)
#             except NameError:
#                 print(f"Error in compute_confidence_l2: {e}")
#                 confidence_value_l2 = 0.5
#             print(l1_sent, l2_sent, confidence_value_l1, confidence_value_l2, cosine_similarity, sep='\t', file=output, flush=True)

# steps/embeddings.py
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import csv

def load_model(model_path=None):
	if model_path is None:
		raise ValueError("You must provide a model_path for embeddings")
	os.environ["TRANSFORMERS_OFFLINE"] = "1"
	print(f"[embeddings] Loading model from {model_path}")
	return SentenceTransformer(model_path)



def add_embeddings(tsv_path, output_path, model):
    """
    Read a TSV file line by line, compute embeddings, and write out to a new TSV
    with cosine similarity.
    """
    with open(tsv_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        # Read header
        header = infile.readline().rstrip("\n")
        # Write header with cosine similarity column
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

            # Compute embeddings
            embeddings = model.encode([l1_sent, l2_sent])
            # Cosine similarity
            cos_sim = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )

            # Write line as-is with similarity
            outfile.write(f"{l1_sent}\t{l2_sent}\t{cos_sim}\n")

