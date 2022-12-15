import pandas as pd
import argparse
import selfies

def selfies_to_smiles(x_selfies):
    x_selfies = x_selfies.replace(" ", "")
    return selfies.decoder(x_selfies)
                
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse mmpdb index output csv.")
    parser.add_argument("--in1", dest="infile1", help="txt file with generated selfies", metavar="input1.txt")
    parser.add_argument("--in2", dest="infile2", help="txt file with original selfies", metavar="input2.txt")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="output.csv")
    args = parser.parse_args()
    print('args')
    
    selfs = [line.strip() for line in open(args.infile1, 'r').readlines()]
    print('selfies')
    original_selfies = [line.strip() for line in open(args.infile2, 'r'). readlines()]
    print('original selfs')
    smi_preds = list(map(selfies_to_smiles, selfs))
    print('smiles')
    orig_smiles = list(map(selfies_to_smiles, original_selfies))
    print('original smiles')
    
    #changed column names so can be inputted into triage.py
    pd.DataFrame({'id':orig_smiles, 'structure':smi_preds}).to_csv(args.outfile, index=False)
