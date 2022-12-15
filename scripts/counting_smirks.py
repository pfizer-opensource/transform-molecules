import pandas as pd
import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Count how many times each smirks occurs in the mmpdb pairs.")
    parser.add_argument("--in", dest="infile", help="comma-delimited input file", metavar="in.csv")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="out.csv")
    args = parser.parse_args()

    smirks = dict()

    with open(args.infile, 'r') as ifs:
        for line in ifs:
            parsed = line.strip().split(',')
            if parsed[4] in smirks:
                smirks[parsed[4]] += 1
            else:
                smirks[parsed[4]] = 1
    df = pd.DataFrame({'smirks':list(smirks.keys()), 'counted':list(smirks.values())})
    df.sort_values(by='counted', ascending=False, inplace=True)
    df.to_csv(args.outfile, index=False)
