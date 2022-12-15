import pandas as pd
import numpy as np
import math
import argparse
import selfies
import re
from scaffolding import get_murcko_scaffold


def smiles_to_selfies(x_smiles, token_sep=True):
    x_selfies = []
    for i in range(x_smiles.shape[0]):
        ax = selfies.encoder(x_smiles[i])
        if ax != -1:
            try:
                if token_sep:
                    sx = re.findall(r"\[[^\]]*\]", ax)
                    ax = " ".join(sx)
                x_selfies.append(ax)
            except:
                x_selfies.append("NaN")
        else:
            x_selfies.append("NaN")
    return x_selfies

def temporal_split(infile, args):
    with open(infile, 'r') as ifs:
        with open(f"{args.outdest}/test.csv", 'w') as test: 
            with open(f"{args.outdest}/train.csv", 'w') as train:
                with open(f"{args.outdest}/val.csv", 'w') as val:
                    train_pairs, val_pairs, test_pairs = set(), set(), set()
                    next(ifs)  # skipping the first line with the header in the input file
                    for line in ifs:
                        smiles1, smiles2, name1, name2, smirk, rgroup = line.strip().split(',')
                        year_name1, year_name2 = years_dict[name1], years_dict[name2]
                        year_name1 = int(year_name1) if not np.isnan(year_name1) else 9999 # all structures without dates have to go to test set to make sure there is no target leak
                        year_name2 = int(year_name2) if not np.isnan(year_name2) else 9999
                        if (name1 in years_dict and name2 in years_dict) and year_name1 < int(args.year1) and year_name2 < int(args.year1):
                            if (name1, name2) not in train_pairs:
                                train_pairs.add((name1, name2))
                                train.write(line)
                            if args.augment:
                                if (name2, name1) not in train_pairs:
                                    train_pairs.add((name2, name1))
                                    train.write(f"{smiles2},{smiles1},{name2},{name1},{smirk.split('>>')[1]}>>{smirk.split('>>')[0]},{rgroup}\n")
                        elif (name1 in years_dict and name2 in years_dict) and year_name1 <= int(args.year2) and year_name2 <= int(args.year2):
                            if (name1, name2) not in val_pairs:
                                val_pairs.add((name1, name2))
                                val.write(line)
                            if args.augment:
                                if (name2, name1) not in val_pairs:
                                    val_pairs.add((name2, name1))
                                    val.write(f"{smiles2},{smiles1},{name2},{name1},{smirk.split('>>')[1]}>>{smirk.split('>>')[0]},{rgroup}\n")
                        else:
                            if (name1, name2) not in test_pairs:
                                test_pairs.add((name1, name2))
                                test.write(line)
                            if args.augment:
                                if (name2, name1) not in test_pairs:
                                    test_pairs.add((name2, name1))
                                    test.write(f"{smiles2},{smiles1},{name2},{name1},{smirk.split('>>')[1]}>>{smirk.split('>>')[0]},{rgroup}\n")

def to_selfies(data, name, outdest):
    data.columns = [0,1]
    smiles1 = np.array(data[0])
    smiles2 = np.array(data[1])
    selfies1 = smiles_to_selfies(smiles1)
    selfies2 = smiles_to_selfies(smiles2)
    with open(f"{outdest}/src-{name}.txt", 'w') as ofs:
        for selfie in selfies1:
            ofs.write(f"{selfie}\n")
    with open(f"{outdest}/tgt-{name}.txt", 'w') as ofs:
        for selfie in selfies2:
            ofs.write(f"{selfie}\n")

def get_train_scaffolds(train_file):
    train = pd.read_csv(train_file, header=None)
    train[6] = train[0].apply(get_murcko_scaffold)
    train[7] = train[1].apply(get_murcko_scaffold)
    train.to_csv(train_file, header=False, index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Split dataset into train, validation and test subsets. Augment if requested.")
    parser.add_argument("--in", dest="infile", help="comma-delimited input file", metavar="in.csv")
    parser.add_argument("--timestamps", dest="timestamps", help="comma-delimited file with years for an earliest publication for each ChEMBL molecule", metavar="all.csv")
    parser.add_argument("--out", dest="outdest", help="output destination")
    # parser.add_argument("--t", dest="percent_train", help="amount to split test-train", default=0.7)
    parser.add_argument("--ids", dest="ids_col", help="name of column with ids", default="chembl_id")
    parser.add_argument("--years", dest="years_col", help="name of column with years", default="year")
    parser.add_argument("--year_train", dest="year1", help="train set will include pairs of molecules, each of which was published before this year (exclusively)", default=2009)
    parser.add_argument("--year_test", dest="year2", help="test set will include pairs of molecules, either or both of which was published after this year (exclusively)", default=2013)
    parser.add_argument("--augment", dest="augment", help="for each (mol1,mol2), add also (mol2,mol1) if not there yet", action='store_true')
    args = parser.parse_args()
    
    years = pd.read_csv(args.timestamps, usecols=[args.ids_col, args.years_col])
    years_dict = {k:v for k,v in zip(list(years[args.ids_col]),list(years[args.years_col]))}
    del years
    print('Starting split')
    temporal_split(args.infile, args)
    
    print('Converting SMILES to SELFIES')
    to_selfies(pd.read_csv(f"{args.outdest}/train.csv", usecols=[0,1]), 'train', args.outdest)
    to_selfies(pd.read_csv(f"{args.outdest}/val.csv", usecols=[0,1]), 'val', args.outdest)
    to_selfies(pd.read_csv(f"{args.outdest}/test.csv", usecols=[0,1]), 'test', args.outdest)
    
    print('Getting training scaffolds')
    get_train_scaffolds(f"{args.outdest}/train.csv")
