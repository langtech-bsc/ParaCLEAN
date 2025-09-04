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
        self.metadata = args.metadata

    def get_paths(self):
        raise NotImplementedError()

    def read(self) -> (str, str):
        raise NotImplementedError()

    def get_size(self):
        with open(self.metadata, 'r') as file:
            config_data = json.load(file)
        size_sentences = config_data.get('size_sentences', '')
        return {
            "size_sentences": size_sentences,
        }

    def get_languages(self):
        with open(self.metadata, 'r') as file:
            config_data = json.load(file)

        languages = config_data.get('languages', [])
        l1 = languages[0] if len(languages) > 0 else ''
        l2 = languages[1] if len(languages) > 1 else ''

        return {"l1": l1, 
                "l2": l2,
        }

    def read_deduplicated(self):

        dataset = [l1_sent.strip() + "\t" + l2_sent.strip() for l1_sent, l2_sent in self.read()] 
        non_dedup_size = len(dataset)
        dataset = list(set(dataset))
        duplicates = non_dedup_size - len(dataset)

        print("There are " + str(duplicates) + " duplicates.")

        return dataset
    
    def write(self, l1_sent, l2_sent, cosine, output):
            print(l1_sent,l2_sent,cosine, sep='\t', file=output)
            

class tmx(IOFormat):

    def get_paths(self):

        with open(self.metadata, 'r') as metadata:
            data = json.load(metadata)
            
        self.paths = {"input": [], "output": None, "format": None}
        for part in data["content"]:
            for raw_path in part["raw_content"]:
                if raw_path.endswith("tmx"):
                    self.paths["input"].append(raw_path)
                    print(self.paths["input"])
        self.paths["output"] = part["destination_path"] + data["identifier"] + ".scored"
        self.paths["format"] = part["destination_path"] + data["identifier"] + ".formatted"
            
        print(self.paths)


    def clean_sentence(self, sentence):
        clean_sent = sentence.replace('\n','')
        return clean_sent

    def convert(self):
        with open(self.paths["format"], 'w') as output:
            for input_file_path in self.paths["input"]:
                languages=self.get_languages()
                l1=languages['l1']
                l2=languages['l2']
                try:
                    context = ET.iterparse(input_file_path, events=("start", "end"))
                    context = iter(context)
                    for event, elem in context:
                        if event == 'end' and elem.tag == 'tu':
                            try:
                                tuv_elements = elem.findall('tuv')
                                if len(tuv_elements) == 2:
                                    l1_text = None
                                    l2_text = None
                                    for tuv in tuv_elements:
                                        lang = tuv.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
                                        seg_text = tuv.find('seg').text.strip()
                                        if lang == l1:
                                            l1_text=seg_text
                                        elif lang == l2:
                                            l2_text=seg_text
                                    output.write(f"{l1_text}\t{l2_text}\n")
                            except AttributeError as e:
                                print(f"Error processing 'tu' element: {ET.tostring(elem, encoding='unicode')}")
                                print(f"AttributeError: {e}")
                            elem.clear()  
                except ET.ParseError as e:
                    print(f"Error parsing {input_file_path}: {e}")


class tsv(IOFormat):

    def get_paths(self):

        with open(self.metadata, 'r') as metadata:
            data = json.load(metadata)
            
        #self.paths = {}
        self.paths = {"input": [], "output": None, "format": None}
        for part in data["content"]:
            for raw_path in part["raw_content"]:
                if raw_path.endswith("tsv"):
                    self.paths["input"].append(raw_path)
                    print(self.paths["input"])
        for part in data["content"]:
            #self.paths["bifixed"][language] = part["destination_path"] + data["identifier"] + ".bifixed"
            self.paths["output"] = part["destination_path"] + data["identifier"] + ".scored"
            self.paths["format"] = part["destination_path"] + data["identifier"] + ".formatted"
        
        print(self.paths)
    
    def convert(self):
        with open('{}'.format(self.paths["format"]), 'w') as output:
            print(args.l1, args.l2, sep='\t', file=output)
            for l1_sent, l2_sent in self.read():
                if l1_sent == '' or l2_sent == '':
                    continue
                print(l1_sent.replace('\t', ' ').replace('\x00', ''), l2_sent.replace('\t', ' ').replace('\x00', ''),sep='\t', file=output)

    def read(self):
        maxInt = sys.maxsize
        while True:
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)
        header = True
        #with open(self.paths["input"], 'r') as file:
        with open(self.paths["input"][0], 'r') as file:
            tsv_file = csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)
            for line_number, element in enumerate(tsv_file, start=1):
                if header:
                    header = False
                    continue
                else:
                    try:
                        l1_sent = element[0].strip()
                        l2_sent = element[1].strip()
                        yield (l1_sent, l2_sent)
                    except Exception as e:
                        print(f"Error occurred at line {line_number}: {e}")
                        print(traceback.format_exc())

    def read_split(self, split):
        maxInt = sys.maxsize
        while True:
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)
        if split == 1:
            header = True
        else:
            header = False
        with open(self.paths["format"].replace('.formatted', f'.formatted.{split:02d}'), 'r') as file:
            tsv_file = csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)
            for line_number, element in enumerate(tsv_file, start=1):
                if header:
                    header = False
                    continue
                else:
                    try:
                        l1_sent = element[0].strip()
                        l2_sent = element[1].strip()
                        yield (l1_sent, l2_sent)
                    except Exception as e:
                        print(f"Error occurred at line {line_number}: {e}")
                        print(traceback.format_exc())


class dual_text(IOFormat):

    def get_paths(self):

        with open(self.metadata, 'r') as metadata:
            data = json.load(metadata)
        
        self.paths = {}
        self.paths["input"] = {}
        for language in data["languages"]:
            for part in data["content"]:
                for raw_path in part["raw_content"]:
                    if raw_path.rsplit(".", 1)[1].strip() == "txt":
                        self.paths["input"]= raw_path
            for part in data["content"]:
                #self.paths["bifixed"][language] = part["destination_path"] + data["identifier"] + ".bifixed"
                self.paths["output"] = part["destination_path"] + data["identifier"] + ".scored"
                self.paths["format"] = part["destination_path"] + data["identifier"] + ".formatted"
        
        print(self.paths)

    def convert(self):
        with open('{}'.format(self.paths["input"]), 'r') as input, open('{}'.format(self.paths["format"]), 'w') as output:
            lines=input.readlines()
            for line in lines:
                print(re.sub(r'\s{2,}', '\t', line.strip()), file=output)
             

class plain_text(IOFormat):

    def get_paths(self):
        with open(self.metadata, 'r') as metadata:
            data = json.load(metadata)

        self.paths = {}
        self.paths["input"] = {}

        for language in data["languages"]:
            for part in data["content"]:
                try:
                    raw_content_paths = part["raw_content"]
                    language_paths = [raw_path for raw_path in raw_content_paths if raw_path.endswith(f'.{language}')]
                    
                    if len(language_paths) > 0:
                        self.paths["input"][language] = language_paths[0]
                        print(f"Language '{language}' file found: {language_paths[0]}")
                    else:
                        print(f"Warning: No matching file found for language '{language}'. Skipping.")
                except IndexError as e:
                    print(f"Error: {e}. Unable to process language '{language}' paths.")

                self.paths["output"] = part["destination_path"] + data["identifier"] + ".scored"
                self.paths["format"] = part["destination_path"] + data["identifier"] + ".formatted"

        print(self.paths)


    def read(self) -> (str, str):

        with open('{}'.format(list(self.paths["input"].values())[0]), 'r') as l1, open('{}'.format(list(self.paths["input"].values())[1]), 'r') as l2:

            for l1_sent, l2_sent in zip(l1, l2):
                l1_sent = l1_sent.strip()
                l2_sent = l2_sent.strip()
                yield (l1_sent, l2_sent)

    def convert(self):
        with open('{}'.format(self.paths["format"]), 'w') as output:
            print(args.l1, args.l2, sep='\t', file=output)
            for l1_sent, l2_sent in self.read():
                if l1_sent == '' or l2_sent == '':
                    continue
                print(l1_sent.replace('\t', ' ').replace('\x00', ''), l2_sent.replace('\t', ' ').replace('\x00', ''),sep='\t', file=output)

    

class raw_csv(IOFormat):

    def get_paths(self):

        # print(metadata_file)

        with open(self.metadata, 'r') as metadata:
            data = json.load(metadata)
        
        self.paths = {}
        self.paths["input"] = {}
        for language in data["languages"]:
            # globals()["l" + str(i)] = language
            for part in data["content"]:
                for raw_path in part["raw_content"]:
                    if raw_path.rsplit(".", 1)[1].strip() == "csv":
                        self.paths["input"][language] = raw_path
                self.paths["output"] = part["destination_path"] + data["identifier"] + ".bifixed"
                self.paths["format"] = part["destination_path"] + data["identifier"] + ".formatted"
                self.paths["tsv"] = part["destination_path"] + data["identifier"] + ".temp.tsv"
        
        print(self.paths)

    def read(self) -> (str, str):

        l1_column = 4
        l2_column = 2
        sep = ","
        header = None

        df = pd.read_csv(list(self.paths["input"].values())[0], sep=sep, header=header)

        for index, row in df.iterrows():
            yield (row[l1_column].strip(), row[l2_column].strip())


def add_base_arguments_to_parser(parser):
    parser.add_argument(
        '--metadata',
        type=str,
        required=True,
        help='Path to the metadata file.'
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
        help='Input format to be used.'
    )
    parser.add_argument(
        '--l2',
        type=str,
        default="pt",
        help='Input format to be used.'
    )



if __name__ == "__main__":

    # parse arguments
    description = """Standardizing formats & extracting variables"""  # TODO: improve description
    parser = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)
    add_base_arguments_to_parser(parser)
    args = parser.parse_args()
    today = date.today()

    # Creating instance based on input format
    if args.input_format == "tsv":
        instance = tsv(args)
        print("data type is TSV")
    elif args.input_format == "plain_text":
        instance = plain_text(args)
        print("data type is plain text")
    elif args.input_format == "dual_text":
        instance = dual_text(args)
        print("data type is dual text")
    elif args.input_format == "raw_csv":
        instance = raw_csv(args)
        print("data type is CSV")
    elif args.input_format == "tmx":
        instance = tmx(args)
        print("data type is TMX")
    else:
        print(f"Error: Unsupported input format - {args.input_format}")
        sys.exit(1)

    instance.get_paths()
    
    instance.convert()

    print(f"formatted={instance.paths['format']}")
    print(f"scored={instance.paths['output']}")
    io_format_instance = IOFormat(args)

    # Call the get_variables function and print the results
    size = io_format_instance.get_size()
    for key, value in size.items():
        print(f"{key}={value}")

    langs = io_format_instance.get_languages()
    for key, value in langs.items():
        print(f"{key}={value}")