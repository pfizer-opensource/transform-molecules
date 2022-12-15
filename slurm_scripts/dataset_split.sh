#!/bin/bash --login
#SBATCH -o .../dataset_split.sh.out
#SBATCH -e .../dataset_split.sh.err
#SBATCH -n 1
#SBATCH -t 10:00:00
#SBATCH --mem-per-cpu=40G

export PYTHONPATH=...
export OE_LICENSE=.../oe_license.txt

mkdir -p $RUN_DIR
cd $RUN_DIR

## Dataset split
echo "Starting dataset split ..."
python ./scripts/dataset_split.py \
    --in $DATA_DIR/${DATA_ID}_filtered.csv \
    --timestamps "$TIMESTAMPS" \
    --out $RUN_DIR \
    --year_train $TRAIN_YEAR \
    --year_test $TEST_YEAR \
    --augment
    
touch src-test.txt src-val.txt tgt-test.txt tgt-val.txt val.csv test.csv  # if all data go to the training subset, this creates empty files for validation and testing
echo "Finished dataset split"

## Generate a single file with all validation molecules, each occurring only once
echo "Starting to generate a file with validation molecules ..."
cat $RUN_DIR/src-val.txt $RUN_DIR/tgt-val.txt | sort | uniq > $RUN_DIR/val-unique.txt
echo "Finished a file with validation molecules"
