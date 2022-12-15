from rdkit.Chem import Crippen
from rdkit.Chem import Lipinski
from rdkit.Chem import Descriptors
from rdkit import Chem
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

def lipinski(smiles):
    mol_wt = []
    hdonors = []
    haccept = []
    logp = []
    for smi in smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            mol_wt.append(pd.NA)
            hdonors.append(pd.NA)
            haccept.append(pd.NA)
            logp.append(pd.NA)
        else:
            hdonors.append(Lipinski.NumHDonors(mol))
            haccept.append(Lipinski.NumHAcceptors(mol))
            mol_wt.append(Descriptors.MolWt(mol))
            logp.append(Crippen.MolLogP(mol))
        
    return mol_wt, hdonors,haccept,logp
    
               
def main():
    parser = argparse.ArgumentParser(description="Get molecular properties of input molecules")
    parser.add_argument("--in", dest="infile", help="csv inputfile with smiles column", metavar="input.csv")
    parser.add_argument("--out", dest="outfile", help="outfile containing molecular properties", metavar="output.csv")
    parser.add_argument("--smi_col", dest="smi_col", help="name of smiles column")
    args = parser.parse_args()
    
    df = pd.read_csv(args.infile)
    mol_wt, hdonors, haccept, logp = lipinski(list(df[args.smi_col]))
    
    df[f'mol_wt_{args.smi_col}'] = mol_wt
    df[f'h_donors_{args.smi_col}'] = hdonors
    df[f'h_acceptors_{args.smi_col}'] = haccept
    df[f'mol_logp_{args.smi_col}'] = logp
    
    df.to_csv(args.outfile, index=False)

if __name__=='__main__':
    main()
