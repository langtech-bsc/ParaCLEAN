import argparse
import hashlib

def hash_line(line):
    return hashlib.md5(line.encode('utf-8')).hexdigest()

def deduplicate_file(input_file, output_file, exclude_file):
    # Read lines from the exclude_file and store their hashes in a set
    exclude_hashes = set()
    
    with open(exclude_file, 'r', encoding='utf-8') as exfile:
        for line in exfile:
            line = line.rstrip('\n')
            line_hash = hash_line(line)
            exclude_hashes.add(line_hash)
    
    # Read lines from the input_file and write to the output_file if not in exclude_hashes
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            line = line.rstrip('\n')
            line_hash = hash_line(line)
            if line_hash not in exclude_hashes:
                outfile.write(line + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deduplicate a file by excluding lines that also appear in another file.')
    parser.add_argument('input_file', help='Path to the input file.')
    parser.add_argument('output_file', help='Path to the output deduplicated file.')
    parser.add_argument('exclude_file', help='Path to the file containing lines to be excluded.')

    args = parser.parse_args()
    deduplicate_file(args.input_file, args.output_file, args.exclude_file)
