from sentence_transformers import SentenceTransformer
import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

os.environ["TRANSFORMERS_OFFLINE"] = "1"
model=SentenceTransformer('***REMOVED***/labse_model')

def add_base_arguments_to_parser(parser):
	parser.add_argument(
		'--input',
		type=str,
		required=True,
		help='Path to txt file of sentences'
	)
	parser.add_argument(
		'--output',
		type=str,
		required=True,
		help='Path to output file'
	)


def embed_sentences(sentence):
	embeddings = model.encode(sentence)
	return embeddings



if __name__ == "__main__":
    description = "Embeds sentences using LaBSE"
    parser = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)
    add_base_arguments_to_parser(parser)
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        sentences = f.readlines()

    embeddings = embed_sentences([sentence.strip() for sentence in sentences])
    embeddings.tofile(args.output)
