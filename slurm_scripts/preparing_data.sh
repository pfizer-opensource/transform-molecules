#!/bin/bash --login
#SBATCH -o .../preparing_data.sh.out
#SBATCH -e .../preparing_data.sh.err
#SBATCH -n 1
#SBATCH -t 20:00:00
#SBATCH --mem-per-cpu=40G

export PYTHONPATH=...
export OE_LICENSE=.../oe_license.txt

mkdir -p $DATA_DIR

## Preparing MMPDB input file
python ./scripts/mmpdb_prep.py \
    --in $DATA \
    --out $DATA_DIR/${DATA_ID}_mmpdb_input.csv \
    --smiles $SMI_COL \
    --ids $ID_COL
    
## Clear stereochemistry
python ./scripts/clear_stereochemistry.py \
    --in $DATA_DIR/${DATA_ID}_mmpdb_input.csv \
    --out $DATA_DIR/${DATA_ID}_mmpdb_input_nostereo.csv

## MMPDB Pairing 
echo "Starting fragmentation ..."
mmpdb fragment \
    --delimiter comma \
    --has-header $DATA_DIR/${DATA_ID}_mmpdb_input_nostereo.csv \
    -o $DATA_DIR/${DATA_ID}.fragments
echo "Finished fragmentation"

echo "Starting pairing..."
mmpdb index $DATA_DIR/${DATA_ID}.fragments \
    -o  $DATA_DIR/${DATA_ID}_pairs.csv \
    --out 'csv'
echo "Finished pairing"

echo "Starting parsing pairs file ..."
python ./scripts/parsing_pairs.py \
    --in $DATA_DIR/${DATA_ID}_pairs.csv \
    --out $DATA_DIR/${DATA_ID}_pairs_parsed.csv
echo "Finished parsing"

rm $DATA_DIR/${DATA_ID}_pairs.csv 

echo "Starting counting smirks ..."
## Counting smirks
python ./scripts/counting_smirks.py \
    --in $DATA_DIR/${DATA_ID}_pairs_parsed.csv\
    --out $DATA_DIR/${DATA_ID}_counted.csv
echo "Finished counting smirks"

echo "Starting filtering data ..."
## Filtering data
python ./scripts/filtering_data.py \
    --in $DATA_DIR/${DATA_ID}_pairs_parsed.csv \
    --all $DATA \
    --smirks $DATA_DIR/${DATA_ID}_counted.csv \
    --out $DATA_DIR/${DATA_ID}_filtered.csv \ 
    --size $SAMPLE_SIZE \
    --exclude $EXCLUDE
echo "Finished filtering data"
