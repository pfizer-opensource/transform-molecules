import pandas as pd
import numpy as np
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse mmpdb index output csv.")
    parser.add_argument("--in", dest="infile", help="whitespace-delimited input file from mmpdb index", metavar="in.csv")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="out.csv")
    args = parser.parse_args()
    pairs_found = set()

    with open(args.infile, 'r') as ifs:
        with open(args.outfile, 'w') as ofs:
            for line in ifs:
                parsed = line.strip().split('\t')
                if (parsed[2],parsed[3]) not in pairs_found and (parsed[3],parsed[2]) not in pairs_found:
                    pairs_found.add((parsed[2],parsed[3]))
                    ofs.write(f"{','.join(parsed)}\n")
