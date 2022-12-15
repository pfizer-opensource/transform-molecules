import argparse
import numpy as np
from openeye import oechem


def clear_stereochemistry(mol):
    clear_atom_stereochemistry(mol)
    clear_bond_sterochemistry(mol)
    oechem.OESuppressHydrogens(mol, False, False, False)

def clear_atom_stereochemistry(mol):
    for atom in mol.GetAtoms():
        chiral = atom.IsChiral()
        stereo = oechem.OEAtomStereo_Undefined
        v = []
        for nbr in atom.GetAtoms():
            v.append(nbr)
        if atom.HasStereoSpecified(oechem.OEAtomStereo_Tetrahedral):
            stereo = atom.GetStereo(v, oechem.OEAtomStereo_Tetrahedral)

        if chiral or stereo != oechem.OEAtomStereo_Undefined:
            atom.SetStereo(v, oechem.OEAtomStereo_Tetrahedral, oechem.OEAtomStereo_Undefined)


def clear_bond_sterochemistry(mol):
    for bond in mol.GetBonds():
        if bond.HasStereoSpecified(oechem.OEBondStereo_CisTrans):
            for atomB in bond.GetBgn().GetAtoms():
                if atomB == bond.GetEnd():
                    continue
                for atomE in bond.GetEnd().GetAtoms():
                    if atomE == bond.GetBgn():
                        continue
                    v = []
                    v.append(atomB)
                    v.append(atomE)
                    stereo = bond.SetStereo(v, oechem.OEBondStereo_CisTrans, oechem.OEBondStereo_Undefined)

def abs_smi(x):
    mol = oechem.OEGraphMol() 
    if oechem.OESmilesToMol(mol, x):
        clear_stereochemistry(mol)
        return oechem.OEMolToSmiles(mol)
    else:
        return np.nan


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Remove stereochemistry from the input data set.")
    parser.add_argument("--in",dest="infile",help="whitespace-delimited input file",metavar="in.csv")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="out.csv")

    args = parser.parse_args()
    n=0
    with open(args.infile, 'r') as ifs:
        with open(args.outfile, 'w') as ofs:
            for line in ifs:
                if n==0:
                    ofs.write(line)
                    n=1
                else:
                    parsed = line.strip().split(',')
                    if ('.' not in parsed[0]):
                        ofs.write(f"{abs_smi(parsed[0])},{parsed[1]}\n")


