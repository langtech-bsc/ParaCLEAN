import argparse

def deduplicate_tsv_by_hash(input_file, output_file, hash_column='bifixer_hash'):
    seen_hashes = set()
    
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        header = infile.readline()
        outfile.write(header)
        
        # Get the index of the hash column
        header_columns = header.rstrip('\n').split('\t')
        hash_index = header_columns.index(hash_column)
        
        for line in infile:
            columns = line.rstrip('\n').split('\t')
            bifixer_hash = columns[hash_index]
            
            if bifixer_hash not in seen_hashes:
                seen_hashes.add(bifixer_hash)
                outfile.write(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deduplicate a TSV file based on a hash column.')
    parser.add_argument('input_file', help='Path to the input TSV file.')
    parser.add_argument('output_file', help='Path to the output deduplicated TSV file.')
    parser.add_argument('--hash_column', default='bifixer_hash', help='Name of the hash column to deduplicate by (default: bifixer_hash).')
    
    args = parser.parse_args()
    deduplicate_tsv_by_hash(args.input_file, args.output_file, args.hash_column)