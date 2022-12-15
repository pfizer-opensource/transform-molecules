import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser(description="Prepare input for mmpdb.")
    parser.add_argument("--in", dest="infile", help="all molecules", metavar="in.csv")
    parser.add_argument("--out", dest="outfile", metavar="out.csv")
    parser.add_argument("--smiles", dest="smiles_col", help="name of column with smiles representations")
    parser.add_argument("--ids", dest="ids_col", help="name of column with ids")
    args = parser.parse_args()
    
    pd.read_csv(args.infile, usecols=[args.smiles_col, args.ids_col])[[args.smiles_col, args.ids_col]].to_csv(args.outfile, index=False)

if __name__=='__main__':
    main()
