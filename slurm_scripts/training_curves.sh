#!/bin/bash --login
#SBATCH -o .../training_curves.sh.out
#SBATCH -e .../training_curves.sh.err
#SBATCH -n 1
#SBATCH -t 1:00:00
#SBATCH --mem-per-cpu=40G

export PYTHONPATH=...

mkdir -p $OUTDEST

python ./scripts/training_curves.py \
    --in $IN_FILE \
    --out $OUTDEST/training_model_info_${MODEL_NUM}.csv \
    --parse_type info

grep 'Validation accuracy' $ERR_FILE > $OUTDEST/${NAME}_${MODEL_NUM}.err

python ./scripts/training_curves.py \
    --in $OUTDEST/${NAME}_${MODEL_NUM}.err \
    --out $OUTDEST/${NAME}_${MODEL_NUM}.csv \
    --name $NAME \
    --parse_type val
    
export NAME=validation_perplexity

grep 'Validation perplexity' $ERR_FILE > $OUTDEST/${NAME}_${MODEL_NUM}.err

python ./scripts/training_curves.py \
    --in $OUTDEST/${NAME}_${MODEL_NUM}.err \
    --out $OUTDEST/${NAME}_${MODEL_NUM}.csv \
    --name $NAME \
    --parse_type val
 
export NAME=training

grep 'Start training loop and validate' $ERR_FILE > $OUTDEST/${NAME}_${MODEL_NUM}.err
grep 'acc:' $ERR_FILE >> $OUTDEST/${NAME}_${MODEL_NUM}.err

python ./scripts/training_curves.py \
    --in $OUTDEST/${NAME}_${MODEL_NUM}.err \
    --out $OUTDEST/${NAME}_${MODEL_NUM}.csv \
    --name $NAME \
    --outpng $OUTDEST \
    --parse_type train

mkdir -p $PLOTDEST
python /gpfs/workspace/users/tysine/Transformer/training_curves.py \
    --val_acc $OUTDEST/validation_accuracy_${MODEL_NUM}.csv \
    --val_ppl $OUTDEST/validation_perplexity_${MODEL_NUM}.csv \
    --train $OUTDEST/training_${MODEL_NUM}.csv \
    --info $OUTDEST/training_model_info_${MODEL_NUM}.csv \
    --metrics $METRICS_TABLE \
    --outpng $PLOTDEST \
    --epoch_cutoff $EPOCH_CUTOFF \
    --parse_type plot
