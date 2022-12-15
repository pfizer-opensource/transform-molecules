#!/bin/bash --login
#SBATCH -o .../plots.sh.out
#SBATCH -e .../plots.sh.err
#SBATCH -n 1
#SBATCH -t 1:00:00
#SBATCH --mem-per-cpu=50G
#SBATCH --gres=gpu:1

export PYTHONPATH=...
export CUDA_VISIBLE_DEVICES=0

## Get molecular properties of input molecules
python ./scripts/molecular_properties.py \
    --in $DATA_DIR/${DATA_ID}_mmpdb_input_nostereo.csv \
    --out $DATA_DIR/${DATA_ID}_molecular_properties.csv \
    --smi_col $SMI_COL
    
python ./scripts/molecular_properties.py \
    --in $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --out $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --smi_col 'structure'

python ./scripts/molecular_properties.py \
    --in $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --out $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --smi_col 'id'

python ./scripts/generating_plots.py \ 
    --in1 $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --in2 $DATA_DIR/${DATA_ID}_molecular_properties.csv \
    --out $PLOT_DIR \ 
    --type molecular_properties \ 
    --smi_col $SMI_COL
