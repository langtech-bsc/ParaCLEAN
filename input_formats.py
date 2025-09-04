import sys
import os
import pandas as pd
import json
from collections import Counter
import csv
import re
import xml.etree.ElementTree as ET
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import date


class IOFormat:

    def __init__(self, args):
        self.input = args.input
        self.output = args.output
        self.format = args.format
        self.l1 = args.l1
        self.l2 = args.l2

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
                                    print(l1_text, l2_text, sep='\t', file=output)
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
    def __init__(self, args):
        # store input/output paths and split index
        self.input = [args.input]       # note: keep as list to match your existing read()
        self.format = args.output       # existing attribute used in convert/read_split
        self.split_index = args.split

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

    # def read_split(self, split):
    #     maxInt = sys.maxsize
    #     while True:
    #         try:
    #             csv.field_size_limit(maxInt)
    #             break
    #         except OverflowError:
    #             maxInt = int(maxInt / 10)

    #     header = split == 1
    #     split_file = self.format.replace('.formatted', f'.formatted.{split:02d}')

    #     with open(split_file, 'r', encoding='utf-8') as file:
    #         tsv_file = csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)
    #         for line_number, element in enumerate(tsv_file, start=1):
    #             if header:
    #                 header = False
    #                 continue
    #             try:
    #                 yield (element[0].strip(), element[1].strip())
    #             except Exception as e:
    #                 print(f"Error occurred at line {line_number}: {e}")


class dual_text(IOFormat):

    def convert(self):
        with open(self.input[0], 'r', encoding='utf-8') as infile, open(self.format, 'w', encoding='utf-8') as output:
            print(self.l1, self.l2, sep='\t', file=output)
            for line_number, line in enumerate(infile, start=1):
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) != 2:
                    print(f"Warning: Skipping line {line_number} due to unexpected format: {line.strip()}")
                    continue
                l1_sent, l2_sent = parts
                print(
                    l1_sent.replace('\t', ' ').replace('\x00', ''),
                    l2_sent.replace('\t', ' ').replace('\x00', ''),
                    sep='\t', file=output
                )

    def read(self):
        with open(self.input[0], 'r', encoding='utf-8') as infile:
            for line_number, line in enumerate(infile, start=1):
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) != 2:
                    print(f"Warning: Skipping line {line_number} due to unexpected format: {line.strip()}")
                    continue
                yield (parts[0].strip(), parts[1].strip())
             
class plain_text(IOFormat):

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

class txt_from_pdf(IOFormat):

    def read(self) -> (str, str):
        # Assumes self.input is a list of two aligned text files
        with open(self.input[0], 'r', encoding='utf-8') as l1_file, \
             open(self.input[1], 'r', encoding='utf-8') as l2_file:
            for line_number, (l1_sent, l2_sent) in enumerate(zip(l1_file, l2_file), start=1):
                try:
                    yield (l1_sent.strip(), l2_sent.strip())
                except Exception as e:
                    print(f"Error at line {line_number}: {e}")

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


class raw_csv(IOFormat):

    def read(self) -> (str, str):
        # Assumes self.input is a list with one CSV file path
        l1_column = 4
        l2_column = 2
        sep = ","
        header = None

        df = pd.read_csv(self.input[0], sep=sep, header=header)

        for _, row in df.iterrows():
            try:
                yield (str(row[l1_column]).strip(), str(row[l2_column]).strip())
            except Exception as e:
                print(f"Skipping row due to error: {e}")

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


def add_base_arguments_to_parser(parser):
    parser.add_argument(
        '--input',
        type=str,
        nargs='+',
        required=True,
        help='Path(s) to the input file(s).'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=False,
        help='Path to the scored output file.'
    )
    parser.add_argument(
        '--format',
        type=str,
        required=False,
        default='formatted.tsv',
        help='Path to the formatted output file. Defaults to "formatted.tsv".'
    )
    parser.add_argument(
        '--input_format',
        type=str,
        default="plain_text",
        help='Input format to be used.'
    )
    parser.add_argument(
        '--l1',
        type=str,
        default="ca",
        help='Source language code.'
    )
    parser.add_argument(
        '--l2',
        type=str,
        default="pt",
        help='Target language code.'
    )



if __name__ == "__main__":

    # parse arguments
    description = "Standardizing formats & extracting variables"
    parser = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)
    add_base_arguments_to_parser(parser)
    args = parser.parse_args()

    # Map input format to class
    format_classes = {
        "tsv": tsv,
        "plain_text": plain_text,
        "dual_text": dual_text,
        "raw_csv": raw_csv,
        "tmx": tmx,
        "txt_from_pdf": txt_from_pdf
    }

    if args.input_format not in format_classes:
        print(f"Error: Unsupported input format - {args.input_format}")
        sys.exit(1)

    # Instantiate and run
    instance = format_classes[args.input_format](args)
    print(f"Data type is {args.input_format}")

    instance.convert()

    if args.input_format:
        print(f"formatted={args.input_format}")
    if args.output:
        print(f"scored={args.output}")

    # Show stats
    size = instance.get_size()
    for key, value in size.items():
        print(f"{key}={value}")

    langs = instance.get_languages()
    for key, value in langs.items():
        print(f"{key}={value}")