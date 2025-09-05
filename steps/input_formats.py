import sys
import os
import pandas as pd
import json
from collections import Counter
import csv
import re
import xml.etree.ElementTree as ET
from datetime import date


class IOFormat:

	def __init__(self, input, output, format, l1, l2):
		self.input = input
		self.output = output
		self.format = format
		self.l1 = l1
		self.l2 = l2

	def read(self) -> (str, str):
		raise NotImplementedError()

	def get_size(self):
		return {
			"size_sentences": sum(1 for _ in self.read())
		}

	def get_languages(self):
		return {"l1": self.l1, "l2": self.l2}

	def read_deduplicated(self):
		dataset = [l1_sent.strip() + "\t" + l2_sent.strip() for l1_sent, l2_sent in self.read()] 
		non_dedup_size = len(dataset)
		dataset = list(set(dataset))
		duplicates = non_dedup_size - len(dataset)
		print(f"There are {duplicates} duplicates.")
		return dataset

	def write(self, l1_sent, l2_sent, cosine, output):
		print(l1_sent, l2_sent, cosine, sep='\t', file=output)
			
class tmx(IOFormat):
	def __init__(self, input_files, output, input_format, l1, l2, split=0):
		self.input = input_files
		self.format = output
		self.split_index = split
		self.l1 = l1
		self.l2 = l2

	def clean_sentence(self, sentence):
		return sentence.replace('\n', '').replace('\t', ' ').replace('\x00', '') if sentence else ''

	def convert(self):
		with open(self.format, 'w', encoding='utf-8') as output:
			print(self.l1, self.l2, sep='\t', file=output)
			for input_file_path in self.input:
				try:
					context = ET.iterparse(input_file_path, events=("start", "end"))
					context = iter(context)
					for event, elem in context:
						if event == 'end' and elem.tag == 'tu':
							try:
								tuv_elements = elem.findall('tuv')
								l1_text = l2_text = None
								for tuv in tuv_elements:
									lang = tuv.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
									seg = tuv.find('seg')
									if seg is None:
										continue
									text = self.clean_sentence(seg.text)
									if lang == self.l1:
										l1_text = text
									elif lang == self.l2:
										l2_text = text
								if l1_text and l2_text:
									print(l1_text, l2_text, sep='\t', file=output, flush=True)
							except AttributeError as e:
								print(f"Error processing 'tu' element: {ET.tostring(elem, encoding='unicode')}")
								print(f"AttributeError: {e}")
							elem.clear()
				except ET.ParseError as e:
					print(f"Error parsing {input_file_path}: {e}")

	def read(self):
		for input_file_path in self.input:
			try:
				context = ET.iterparse(input_file_path, events=("start", "end"))
				context = iter(context)
				for event, elem in context:
					if event == 'end' and elem.tag == 'tu':
						try:
							tuv_elements = elem.findall('tuv')
							l1_text = l2_text = None
							for tuv in tuv_elements:
								lang = tuv.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
								seg = tuv.find('seg')
								if seg is None:
									continue
								text = self.clean_sentence(seg.text)
								if lang == self.l1:
									l1_text = text
								elif lang == self.l2:
									l2_text = text
							if l1_text and l2_text:
								yield (l1_text, l2_text)
						except AttributeError as e:
							print(f"Error processing 'tu': {ET.tostring(elem, encoding='unicode')}")
						elem.clear()
			except ET.ParseError as e:
				print(f"Error parsing {input_file_path}: {e}")

class tsv(IOFormat):
	def __init__(self, input_files, output, input_format, l1, l2, split=0):
		self.input = input_files
		self.format = output
		self.split_index = split
		self.l1 = l1
		self.l2 = l2

	def get_paths(self):
		# needed by scoring script
		self.paths = {
			"input": self.input[0],
			"output": self.format
		}

	# keep your existing methods
	def convert(self):
		with open(self.format, 'w', encoding='utf-8') as output:
			print(self.l1, self.l2, sep='\t', file=output)
			for l1_sent, l2_sent in self.read():
				if l1_sent == '' or l2_sent == '':
					continue
				print(
					l1_sent.replace('\t', ' ').replace('\x00', ''),
					l2_sent.replace('\t', ' ').replace('\x00', ''),
					sep='\t', file=output
				)

	def read(self):
		maxInt = sys.maxsize
		while True:
			try:
				csv.field_size_limit(maxInt)
				break
			except OverflowError:
				maxInt = int(maxInt / 10)

		with open(self.input[0], 'r', encoding='utf-8') as file:
			tsv_file = csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)
			next(tsv_file, None)  # Skip header
			for line_number, element in enumerate(tsv_file, start=1):
				try:
					yield (element[0].strip(), element[1].strip())
				except Exception as e:
					print(f"Error at line {line_number}: {e}")

	def read_split(self, split):
		"""
		Reads a single split file. Assumes self.input[0] is already the split file.
		The 'split' argument is only used for bookkeeping (e.g., header handling).
		"""
		maxInt = sys.maxsize
		while True:
			try:
				csv.field_size_limit(maxInt)
				break
			except OverflowError:
				maxInt = int(maxInt / 10)

		header = split == 1  # If first split, optionally skip header
		with open(self.input[0], 'r', encoding='utf-8') as file:
			tsv_file = csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)
			for line_number, element in enumerate(tsv_file, start=1):
				if header:
					header = False
					continue
				try:
					yield element[0].strip(), element[1].strip()
				except Exception as e:
					print(f"Error at line {line_number}: {e}")


class plain_text(IOFormat):
	def __init__(self, input_files, output, input_format, l1, l2, split=0):
		# input_files should be a list of two files
		if isinstance(input_files, str):
			self.input = [input_files]
		else:
			self.input = input_files
		if len(self.input) != 2:
			raise ValueError("plain_text format expects exactly 2 input files for parallel corpora.")
		self.format = output
		self.l1 = l1
		self.l2 = l2
		self.split_index = split

	def convert(self):
		with open(self.format, 'w', encoding='utf-8') as output:
			print(self.l1, self.l2, sep='\t', file=output)
			for l1_sent, l2_sent in self.read():
				if l1_sent == '' or l2_sent == '':
					continue
				print(
					l1_sent.replace('\t', ' ').replace('\x00', ''),
					l2_sent.replace('\t', ' ').replace('\x00', ''),
					sep='\t', file=output
				)

	def read(self):
		with open(self.input[0], 'r', encoding='utf-8') as file1, \
			 open(self.input[1], 'r', encoding='utf-8') as file2:
			for line_number, (l1_sent, l2_sent) in enumerate(zip(file1, file2), start=1):
				try:
					yield (l1_sent.strip(), l2_sent.strip())
				except Exception as e:
					print(f"Error at line {line_number}: {e}")

	def read_split(self, split):
		header = split == 1
		split_file = self.format.replace('.formatted', f'.formatted.{split:02d}')
		
		with open(split_file, 'r', encoding='utf-8') as file:
			for line_number, line in enumerate(file, start=1):
				if header:
					header = False
					continue
				try:
					l1_sent, l2_sent = line.rstrip('\n').split('\t')
					yield (l1_sent.strip(), l2_sent.strip())
				except Exception as e:
					print(f"Error at line {line_number}: {e}")

format_classes = {
	"tsv": tsv,
	"plain_text": plain_text,
	"tmx": tmx,

}

def run(input_files, l1, l2, input_format="plain_text", output="formatted.tsv"):
	if input_format not in format_classes:
		raise ValueError(f"Unsupported input format: {input_format}")

	cls = format_classes[input_format]
	if isinstance(input_files, str):
		input_files = [input_files]

	instance =  cls(input_files, output, input_format, l1, l2)
	instance.convert()
	return output

def save(data, output_path):
	"""
	Save a list of dicts with 'l1' and 'l2' keys to a TSV.
	"""
	with open(output_path, "w", encoding="utf-8") as f:
		f.write("l1\tl2\n")
		for record in data:
			f.write(f"{record['l1']}\t{record['l2']}\n")
