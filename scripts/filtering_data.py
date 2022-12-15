import pandas as pd
import numpy as np
import random
import argparse

def main(args):
    #generating dictionary of smirks and their counts for the top N widespread transformations
    count_df = pd.read_csv(args.smirks, header=None)
    count_df.drop(index=count_df.index[0],axis=0,inplace=True)
    count_df.columns = ['smirks','counted']
    count_df['counted'] = np.int64(count_df['counted'])
    count_df.sort_values(by='counted',ascending=False, inplace=True)
    
    smirk_counts = dict(zip(list(count_df['smirks']), list(count_df['counted'])))
    
    exclude = count_df[count_df['counted'] < int(args.exclude)]
    smirk_exclude = set(exclude['smirks'])
    
    
    #getting dictionary of target tid to chembl_id if filtering by a target
    if args.target != None:
        tid_df = pd.read_csv(args.target_dict, usecols=['tid', 'chembl_id'])
        tid_dict = dict(zip(list(tid_df['chembl_id']), list(tid_df['tid'])))
        target_id = tid_dict[args.target]
        del tid_df
        all_df = pd.read_csv(args.alldata, usecols=['chembl_id', 'tid'])
        chembl_dict = dict(zip(list(all_df['chembl_id']), list(all_df['tid']))) 
        del all_df
    
    #getting indices of all smirks and exclude those pairs with a molecule that targets the target
    with open(args.infile, 'r') as ifs:
        smirk_indices = {k:[] for k in list(smirk_counts.keys())}
        for index, line in enumerate(ifs):
            _,_,id1,id2,smirk,_ = line.strip().split(',')
            if smirk in smirk_indices:
                if args.target == None or (chembl_dict[id1] != target_id and chembl_dict[id2] != target_id):
                    smirk_indices[smirk].append(index)
                else:
                    print(f'exclude by target: {index}')
               
    #randomly selecting indices for downsampling
    smirk_downsampled = dict()
    for smr, indices in smirk_indices.items():
        if not args.sample or len(indices) < int(args.sample):
            smirk_downsampled[smr] = indices
        else:
            smirk_downsampled[smr] = random.sample(indices, int(args.sample))
    
    #write sampled pairs to outfile
    with open(args.infile, 'r') as ifs:
        with open(args.outfile, 'w') as ofs:
            for index, line in enumerate(ifs):
                _,_,_,_,smirk,_ = line.strip().split(',')
                if smirk not in smirk_exclude:
                    if (smirk in smirk_downsampled and index in smirk_downsampled[smirk]) or (smirk not in smirk_downsampled):
                        ofs.write(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Filters and downsamples the data based on smirk counts.")
    parser.add_argument("--in", dest="infile", help="comma-delimited input file", metavar="in.csv")
    parser.add_argument("--all", dest="alldata", help="comma-delimited file with all chembl_data", metavar="all.csv")
    parser.add_argument("--smirks", dest="smirks", help="file with counts of smirks in infile", metavar="smirks.csv")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="out.csv")
    parser.add_argument("--size", dest="sample", help="number to sample from each smirk", default=None)
    parser.add_argument("--exclude", dest="exclude", help="threshold to exclude smirks at", default=2)
    parser.add_argument("--target", dest="target", help="chembl_id of target to exclude", default=None)
    parser.add_argument("--tid", dest="target_dict", help="location of target_dictionary from chembl_id", default=None)
    args = parser.parse_args()

    main(args)
