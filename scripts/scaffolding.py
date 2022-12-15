import pandas as pd
import argparse
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import *

def get_murcko_scaffold(smi):
    mol = MolFromSmiles(smi)
    if not mol:
        return ""
    return MolToSmiles(MurckoScaffold.GetScaffoldForMol(mol))

def get_canonical_smiles(x):
    mol = oechem.OEGraphMol()
    oechem.OESmilesToMol(mol, x)
    return oechem.OECreateCanSmiString(mol)

def main():
    parser = argparse.ArgumentParser(description="Make scaffold of input molecules")
    parser.add_argument("--in", dest="infile", help="comma-delimited input file of original and predicted smiles", metavar="input.txt")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="output.csv")
    parser.add_argument("--column1", dest="column1", help="Name of column with smiles")
    parser.add_argument("--column2", dest="column2", help="Name of column with smiles", default=False)
    args = parser.parse_args()
    
    df = pd.read_csv(args.infile)
    df = df[df[args.column1].apply(pd.isna)==False]
    if args.column2:
        df = df[df[args.column2].apply(pd.isna)==False]
        df[args.column2+'_canonical'] = df[args.column2].apply(get_canonical_smiles)
        df[args.column2+'_scaffold'] = df[args.column2+'_canonical'].apply(get_murcko_scaffold)
    df[args.column1+'_canonical'] = df[args.column1].apply(get_canonical_smiles)
    df[args.column1+'_scaffold'] = df[args.column1+'_canonical'].apply(get_murcko_scaffold)  
    df.to_csv(args.outfile, index=False)

if __name__=='__main__':
    main()
