import numpy as np
import pandas as pd
import argparse
import random
from operator import itemgetter
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, PandasTools 
from rdkit.Chem.AtomPairs import Pairs

def temporal_split(df, outdest, target):
    df.sort_values(by='year', inplace=True)
    temporal_df = df[df['year'].notna()]
    top_50 = int(round(temporal_df.shape[0]/2))
    temporal_df.head(top_50).to_csv(f"{outdest}/early_years_{target}.csv")
    temporal_df.tail(temporal_df.shape[0]-top_50).to_csv(f"{outdest}/later_years_{target}.csv)

def activity_split(df, outdest, target):
    df.sort_values(by=args.activity_col, inplace=True)
    activity_df = df[df[args.activity_col].notna()]
    top_50 = int(round(temporal_df.shape[0]*0.05))
    activity_df.head(top_50).to_csv(f"{outdest}/most_active_{target}.csv")
    activity_df.tail(temporal_df.shape[0]-top_50).to_csv(f"{outdest}/least_active_{target}.csv)                                                                                                 

def fp_2D(smi, fptype='ECPF4'):
    m1 = Chem.MolFromSmiles(smi)
    if not m1:
        print(f"RDKit was unable to parse {smi}.", file=sys.stderr)
        return None

    if fptype=='ECFP4':
        return AllChem.GetMorganFingerprint(m1, 2)
    elif fptype=='ECFP6':
        return AllChem.GetMorganFingerprint(m1, 3)
    elif fptype=='AP':
        return Pairs.GetAtomPairFingerprint(m1)
    else:
        raise NotImplementedError(f"Fingerprint type {fptype} is not implemented.")
        
def tanimoto_similarity(fp1, fp2):
    if (fp1 is not None) and (fp2 is not None):
        result = DataStructs.TanimotoSimilarity(fp1, fp2)
    else:
        result = 0.0
    return result

def tanimoto_similarity_from_smiles(smi1, smi2, fptype='ECFP4'):
    fp1 = fp_2D(smi1, fptype)
    fp2 = fp_2D(smi2, fptype)
    return tanimoto_similarity(fp1, fp2)


def calculate_tanimoto_similarity(actual, pred, dic):
    top_scores = []
    for sm1 in actual:
        top = list(max([(sm1, sm2, tanimoto_similarity_from_smiles(sm1, sm2)) for sm2 in pred if type(sm2)==str], key=itemgetter(2)))
        top_scores.append(top+[dic[top[1]]])
    return top_scores

def generate_png(df):
    for n in range(df.shape[0]):
        actual, pred, tani, inpt = df.loc[n]
        
        mol = oechem.OEGraphMol() 
        oechem.OESmilesToMol(mol, actual)
        simple_png1 = f"{args.png_dest}/experimental_{n}.png"
        oedepict.OEPrepareDepiction(mol)
        width, height = 600,600
        opts = oedepict.OE2DMolDisplayOptions(width,height,oedepict.OEScale_Default*10)
        opts.SetTitleLocation(oedepict.OETitleLocation_Hidden)
        disp = oedepict.OE2DMolDisplay(mol, opts)
        oedepict.OERenderMolecule(simple_png1, disp)

        mol = oechem.OEGraphMol() 
        oechem.OESmilesToMol(mol, pred)
        simple_png2 = f"{args.png_dest}/generated_{n}.png"
        oedepict.OEPrepareDepiction(mol)
        width, height = 600,600
        opts = oedepict.OE2DMolDisplayOptions(width,height,oedepict.OEScale_Default*10)
        opts.SetTitleLocation(oedepict.OETitleLocation_Hidden)
        disp = oedepict.OE2DMolDisplay(mol, opts)
        oedepict.OERenderMolecule(simple_png2, disp)   
        
        mol = oechem.OEGraphMol() 
        oechem.OESmilesToMol(mol, inpt)
        simple_png1 = f"{args.png_dest}/input_{n}.png"
        oedepict.OEPrepareDepiction(mol)
        width, height = 600,600
        opts = oedepict.OE2DMolDisplayOptions(width,height,oedepict.OEScale_Default*10)
        opts.SetTitleLocation(oedepict.OETitleLocation_Hidden)
        disp = oedepict.OE2DMolDisplay(mol, opts)
        oedepict.OERenderMolecule(simple_png1, disp)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Python scripts part of target-specific data pipeline")
    parser.add_argument("--in1", dest="infile1", help="actual target molecules", metavar="in1.csv")
    parser.add_argument("--in2", dest="infile2", help="pred target molecules", metavar="in2.csv")
    parser.add_argument("--smi_col", dest="smi_col", help="name of column with smiles in actual target molecules")
    parser.add_argument("--out", dest="outfile", metavar="out.csv")
    parser.add_argument("--outdest", dest="outdest")
    parser.add_argument("--png_dest", dest="png_dest")
    parser.add_argument("--target", dest="target", help="chembl_id of target to exclude", default=None)
    parser.add_argument("--target_name", dest="target_name", help="name of target", default=None)
    parser.add_argument("--tid", dest="target_dict", help="location of target_dictionary from chembl_id", default=None)
    parser.add_argument("--generate_png", dest="generate_png", action='store_true')
    parser.add_argument("--data_split", dest="data_split", action='store_true')
    args = parser.parse_args()
    
    if args.data_split:
        tid_df = pd.read_csv(args.target_dict, usecols=['tid', 'chembl_id'])
        tid_dict = dict(zip(list(tid_df['chembl_id']), list(tid_df['tid'])))
        target_id = tid_dict[args.target]
        del tid_df
        all_df = pd.read_csv(args.alldata, usecols=['chembl_id', 'tid'])
        chembl_dict = dict(zip(list(all_df['chembl_id']), list(all_df['tid']))) 
        del all_df
        
    
        with open(args.infile, 'r') as ifs:
            with open(args.outfile, 'w') as ofs:
                for line in ifs:
                    parsed = line.strip().split(',')
                    if parsed[4] == target_id:
                        ofs.write(line)

        data_df = pd.read_csv(args.outfile)
        temporal_split(data_df, args.outdest, args.target_name)
        activity_split(data_df, args.outdest, args.target_name)

    if args.generate_png:
        pred = pd.read_csv(args.infile2)
        in_out_dict = dict(zip(list(pred['structure']),list(pred['id'])))
        actual = pd.read_csv(args.infile1, usecols=[args.smi_col])
        tnm_list = calculate_tanimoto_similarity(list(actual[args.smi_col]), list(pred['structure']), in_out_dict)
        tnm_df = pd.DataFrame(tnm_list, columns=['Actual', 'Prediction', 'Tanimoto', 'Input'])
        tnm_df.to_csv(args.outfile, index=False)
        generate_png(tnm_df)
