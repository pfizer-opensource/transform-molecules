#!/bin/bash --login
#SBATCH -o .../predictions.sh.out
#SBATCH -e .../predictions.sh.err
# #SBATCH -n 
#SBATCH -t 1:00:00
#SBATCH --mem-per-cpu=25G
#SBATCH --gres=gpu:1

export PYTHONPATH=...
export OE_LICENSE=.../oe_license.txt

export CUDA_VISIBLE_DEVICES=0

mkdir -p $OUTPUT_DIR

echo 'Starting Translate ...'
if [ ! -s $OUTPUT_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt ]; then
    onmt_translate \
        --model $MODEL_DIR/${MODEL_ID}_epoch_${EPOCH_NUM}.pt \
        --src $RUN_DIR/val-unique.txt \
        --output $OUTPUT_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt \
        --replace_unk \
        --seed 1 \
        --gpu 0
fi
echo 'Finished Translate'


## Convert selfies to smiles
echo "Starting SELFILES to SMILES ..."
python ./scripts/selfies_to_smiles.py \
    --in1 $OUTPUT_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt \
    --in2 $RUN_DIR/val-unique.txt \
    --out $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv
echo "Finished SELFILES to SMILES"
 
python ./scripts/scaffolding.py \
    --in $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --out $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --column1 'structure' \
    --column2 'id'
    
## Score model predictions
python ./scripts/scoring.py \
    --in $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \
    --metrics_table $METRICS_TABLE \
    --training_data $RUN_DIR/train.csv \
    --model ${MODEL_ID}_epoch_${EPOCH_NUM} \
    --change_count \
    --scaffolds

# ## Generate pngs of predicted smiles
# singularity run --nv $SINGULARITY_CONTAINER mkdir /gpfs/workspace/users/tysine/images/${MODEL_ID}_epoch_$EPOCH_NUM

# singularity run --nv $SINGULARITY_CONTAINER shuf $DATA_DIR/pred_smiles_epoch_${EPOCH_NUM}_unique.csv | head -100 > $DATA_DIR/pred_smiles_epoch_${EPOCH_NUM}_100.csv

# singularity run --nv $SINGULARITY_CONTAINER python /gpfs/workspace/users/tysine/Transformer/visualize_smiles.py \
#     --in $DATA_DIR/pred_smiles_epoch_${EPOCH_NUM}_100.csv \
#     --out /gpfs/workspace/users/tysine/images/${MODEL_ID}_epoch_$EPOCH_NUM
