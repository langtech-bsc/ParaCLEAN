import pandas as pd
import argparse
import os
import numpy as np
import sys
import tempfile

def filter_corpus(corpus_file, filtered_output_file, discarded_output_file, header_written=False, target_sample_size=float('inf'), total_samples=0):
    print('Starting processing corpus:', corpus_file, flush=True)
    is_header=True
    lines_added=0
    
    with open(corpus_file, 'r') as file, \
        open(filtered_output_file, 'a' if os.path.exists(filtered_output_file) else 'w') as filtered_output, \
        open(discarded_output_file, 'a' if os.path.exists(discarded_output_file) else 'w') as discarded_output:

        if not header_written:
            filtered_output.write(f"{args.l1}\t{args.l2}\n")
            discarded_output.write(f"{args.l1}\t{args.l2}\tl1_prob\tl2_prob\talignment\n")
            header_written = True
            
        for line in file:
            # Stop sampling if we've reached the target sample size
            if total_samples >= target_sample_size:
                print("Target sample size reached.")
                return header_written, total_samples

            if is_header:     
                is_header = False
                continue

            try:
                row = line.strip().split('\t')
                alignment = float(row[4])
                l1_prob = float(row[2])
                l2_prob = float(row[3])
                
                if alignment >= float(args.threshold) and \
                   l1_prob >= float(args.l1_probability) and \
                   l2_prob >= float(args.l2_probability):
                    filtered_output.write('\t'.join(row[:2]) + '\n')
                    lines_added += 1
                    total_samples += 1  # Increment the total sample count
                else:
                    failed_conditions = []
                    if alignment < float(args.threshold):
                        failed_conditions.append(f"Alignment ({alignment}) < Threshold ({args.threshold})")
                    if l1_prob < float(args.l1_probability):
                        failed_conditions.append(f"L1 Probability ({l1_prob}) < L1 Probability Threshold ({args.l1_probability})")
                    if l2_prob < float(args.l2_probability):
                        failed_conditions.append(f"L2 Probability ({l2_prob}) < L2 Probability Threshold ({args.l2_probability})")
                    
                    failed_conditions_str = ", ".join(failed_conditions)
                    discarded_output.write('\t'.join(row) + f" (Failed conditions: {failed_conditions_str})\n")
            except Exception as e:
                print(f"Error processing line {line} in corpus {corpus_file}: {e}")

    print(f"{lines_added} segments were taken from ", corpus_file, flush=True)
    return header_written, total_samples

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", help="corpus or corpora from which to sample. Add as many as needed.", nargs="+")
    parser.add_argument("--sample_output_path",  help="folder where to write the sample", required=True)
    parser.add_argument("--l1", required=True)
    parser.add_argument("--l2", required=True)
    parser.add_argument("-t", "--threshold", required=False, default=.75)
    parser.add_argument("-l1p", "--l1_probability", required=False, default=.5)
    parser.add_argument("-l2p", "--l2_probability", required=False, default=.5)
    parser.add_argument("--sample_size", type=int, required=False, default=None, help="Desired sample size")

    args = parser.parse_args()
    print(float(args.l1_probability))
    print(float(args.l2_probability))
    print(float(args.threshold))

    if not args.l1:
        parser.error('Please specify corpus languages with the --l1 and --l2 options')
    elif not args.l2:
        parser.error('Please specify corpus languages with the --l1 and --l2 options')

    # Set the target sample size (unlimited if None)
    target_sample_size = args.sample_size if args.sample_size is not None else float('inf')

    header_written = False
    filtered_output_file = os.path.join(args.sample_output_path, f"filtered_corpus.{args.l1}-{args.l2}")
    discarded_output_file = os.path.join(args.sample_output_path, f"discarded_corpus.{args.l1}-{args.l2}")

    # Remove existing files if they exist
    if os.path.exists(filtered_output_file):
        os.remove(filtered_output_file)

    if os.path.exists(discarded_output_file):
        os.remove(discarded_output_file)

    # Initialize total sample counter
    total_samples = 0

    # Process each corpus until reaching the sample size limit
    for corpus in args.corpus:
        header_written, total_samples = filter_corpus(corpus, filtered_output_file, discarded_output_file, 
                                                      header_written, target_sample_size, total_samples)
        
        print(f'Finished filtering corpus: {corpus}', flush=True)

        # Stop further processing if target sample size has been reached
        if total_samples >= target_sample_size:
            print("Sample size limit reached, stopping further processing.")
            break
