import sys
from os import path

def get_sent(index,file):
    index = index.replace('[','').replace(']','')
    if ',' in index:
        indeces = [int(subindex) for subindex in index.split(', ')]
        sentence = ' '.join([file[indeces[0]],file[indeces[1]]])
    elif index == '':
        sentence = ''
    else:
        sentence = file[int(index)]
    return sentence

def process_alignments(log, source, target, out):
    #print(out)
    aligned_sentences = []
    log = open(log,'r').read().splitlines()
    en_file = open(source,'r').read().splitlines()
    ca_file = open(target,'r').read().splitlines()
    write_out = open(out,'w')
    for line in log:
        src_idx, tgt_idx, score = line.split(':')   
        en_sent = get_sent(src_idx, en_file).replace('\t',' ')
        ca_sent = get_sent(tgt_idx, ca_file).replace('\t',' ')
        #print(('\t'.join([ca_sent, en_sent, score])))
        aligned_sentences.append('\t'.join([ca_sent, en_sent, score]))
    for line in aligned_sentences:
        write_out.write(line+'\n')

def main():
    log = sys.argv[1]
    source = sys.argv[2]
    target = sys.argv[3]
    out = sys.argv[4]
    # process files and write them to the output folder
    process_alignments(log, source, target, out)

if __name__ == "__main__":
    main()