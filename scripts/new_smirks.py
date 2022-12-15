import sys
import pandas as pd
import numpy as np
import argparse
import subprocess
from openeye import oechem, oedepict

def make_smi_df(infile, outfile):
    inf = pd.read_csv(infile)
    otf = inf['id'].append(inf['structure'], ignore_index=True)
    otf = pd.DataFrame({'smiles':otf, 'id':range(otf.shape[0])})
    otf.to_csv(outfile, index=False, header=False)

def get_smirks(infile1, infile2, outfile):
    all_smirks = pd.read_csv(infile1)
    all_smirks.columns = ['id', 'structure', 'ch1', 'ch2', 'smirk', 'other']
    all_smirks.drop(columns=['ch1','ch2','other'], inplace=True)
    generated_pairs = pd.read_csv(infile2)
    generated_pairs = generated_pairs.merge(all_smirks, how='left', left_on=['id','structure'], right_on=['id','structure'])
    generated_pairs.to_csv(outfile, index=False)
    

def counting_smirks(infile, training):
    training_smirks = set(n for n in list(pd.read_csv(training)['smirks']))
    smirks_dict = dict()
    
    for n in list(pd.read_csv(infile)['smirk']):
        if n not in training_smirks and n != np.nan:
            if n not in smirks_dict:
                smirks_dict[n] = 1
            else:
                smirks_dict[n] += 1
    return len(smirks_dict), sum(list(smirks_dict.values())), smirks_dict
 
def generate_png(args, df):
    for n in range(df.shape[0]):
        if df.loc[n,'counted']>=int(args.threshold) and type(df.loc[n,'smirks'])==str:
            smiles1, smiles2 = df.loc[n,'smirks'].split('>>')

            mol = oechem.OEGraphMol() 
            oechem.OESmilesToMol(mol, smiles1)
            simple_png1 = f"{args.png_dest}/smirk1_{n}.png"
            oedepict.OEPrepareDepiction(mol)
            width, height = 600,600
            opts = oedepict.OE2DMolDisplayOptions(width,height,oedepict.OEScale_Default*10)
            opts.SetTitleLocation(oedepict.OETitleLocation_Hidden)
            disp = oedepict.OE2DMolDisplay(mol, opts)
            oedepict.OERenderMolecule(simple_png1, disp)

            mol = oechem.OEGraphMol() 
            oechem.OESmilesToMol(mol, smiles2)
            simple_png2 = f"{args.png_dest}/smirk2_{n}.png"
            oedepict.OEPrepareDepiction(mol)
            width, height = 600,600
            if smiles2 == '[*:1][H]':
                opts = oedepict.OE2DMolDisplayOptions(width,height,oedepict.OEScale_Default*7)
            else:
                opts = oedepict.OE2DMolDisplayOptions(width,height,oedepict.OEScale_Default*10)
            opts.SetTitleLocation(oedepict.OETitleLocation_Hidden)
            disp = oedepict.OE2DMolDisplay(mol, opts)
            oedepict.OERenderMolecule(simple_png2, disp)                                                                                                        

def main():
    parser = argparse.ArgumentParser(description="Get smirks of model predictions")
    parser.add_argument("--in", dest="infile", help="csv file with input dependent on which function {make_smi_df, get_smirks, new_smirks} is called", metavar="input.txt")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="output.csv")
    parser.add_argument("--in2", dest="infile2", help="second csv infile dependent on which function {get_smirks, new_smirks} is called", metavar="infile2.csv")
    parser.add_argument("--training", dest="training", help="original training file", metavar="training.csv")
    parser.add_argument("--make_smi_df", dest="make_smi_df", help="run function to generate all smiles csv", action='store_true')
    parser.add_argument("--get_smirks", dest="get_smirks", help="run function to get smirks of generated pairs", action='store_true')
    parser.add_argument("--new_smirks", dest="new_smirks", help="run function to count new smirks", action='store_true')
    parser.add_argument("--threshold", dest="threshold", help="smirk count threshold to generate pngs", default=1000)
    parser.add_argument("--png_dest", dest="png_dest", help="directory to save smirk pngs")
    args = parser.parse_args()
    
    if args.make_smi_df:
        make_smi_df(args.infile, args.outfile)
    elif args.get_smirks:
        get_smirks(args.infile, args.infile2, args.outfile)
    elif args.new_smirks:
        n_unique_smirks, n_all_smirks, smirk_dict = counting_smirks(args.infile, args.infile2)
        count_df = pd.DataFrame({'smirks':list(smirk_dict.keys()), 'counted': list(smirk_dict.values())})
        count_df.sort_values(by='counted', inplace=True, ascending=False)
        count_df.to_csv(args.outfile, index=False)
        generate_png(args, count_df)

if __name__=='__main__':
    main()
