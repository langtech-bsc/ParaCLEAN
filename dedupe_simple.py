import argparse
import hashlib

def hash_line(line):
    return hashlib.md5(line.encode('utf-8')).hexdigest()

def deduplicate_file(input_file, output_file, duplicates_file):
    seen_hashes = set()
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile, \
         open(output_file, 'w', encoding='utf-8') as deduped_out, \
         open(duplicates_file, 'w', encoding='utf-8') as dupes_out:

        for line in infile:
            line = line.rstrip('\n')
            line_hash = hash_line(line)
            if line_hash not in seen_hashes:
                seen_hashes.add(line_hash)
                deduped_out.write(line + '\n')  # Write unique lines to output_file
            else:
                dupes_out.write(line + '\n')  # Write duplicates to duplicates_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deduplicate a parallel corpus.')
    parser.add_argument('input_file', help='Path to the input file.')
    parser.add_argument('output_file', help='Path to the output deduplicated file.')
    parser.add_argument('duplicates_file', help='Path to file showing duplicated lines.')

    args = parser.parse_args()
    deduplicate_file(args.input_file, args.output_file, args.duplicates_file)
