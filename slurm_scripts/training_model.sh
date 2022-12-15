#!/bin/bash --login
#SBATCH -o .../training.sh.out
#SBATCH -e .../training.sh.err
#SBATCH -n 1
#SBATCH -t 4-00:00:00
#SBATCH --mem-per-cpu=50G
#SBATCH --gres=gpu:1

#export PYTHONPATH=...
export CUDA_VISIBLE_DEVICES=0

mkdir -p $MODEL_DIR 

## Calculate Train size, train steps and save steps
export TRAIN_SIZE=$(cat $RUN_DIR/src-train.txt | wc -l)
export EPOCH_STEPS=$(($TRAIN_SIZE/$BATCH_SIZE))
export TRAIN_STEPS=$(($EPOCH_STEPS*$TRAIN_EPOCHS))
export SAVE_STEPS=$(($EPOCH_STEPS*$SAVE_EPOCHS))

# if validation set is not empty, run validation at the end of each epoch; otherwise, don't run during training
export VS=$(head $RUN_DIR/src-val.txt | wc -l)
if [ $VS -eq 0 ]; then
  export VALID_STEPS=$(($TRAIN_STEPS+1))
else
  export VALID_STEPS=$EPOCH_STEPS
fi

## Build config yaml
cat << EOF > $RUN_DIR/config.yaml
## Where the vocab(s) will be written
src_vocab: $RUN_DIR/vocab.src
tgt_vocab: $RUN_DIR/vocab.tgt

# Corpus opts:
data:
    corpus_1:
        path_src: $RUN_DIR/src-train.txt
        path_tgt: $RUN_DIR/tgt-train.txt
    valid:
        path_src: $RUN_DIR/src-val.txt
        path_tgt: $RUN_DIR/tgt-val.txt
EOF

## OpenNMT preprocessing data
onmt_build_vocab \
    -config $RUN_DIR/config.yaml \
    -save_data $RUN_DIR/data \
    -n_samples -1
 
## OpenNMT Training Model 
onmt_train \
    -config $RUN_DIR/config.yaml \
    -save_model $MODEL_DIR/$MODEL_ID \
    -train_steps $TRAIN_STEPS \
    -valid_steps $VALID_STEPS \
    -save_checkpoint_steps $SAVE_STEPS \
    -batch_size $BATCH_SIZE \
    -world_size 1 \
    -gpu_ranks 0 
    
## Rename models from steps to epochs
python ./scripts/renaming_models.py \
    --models $MODEL_DIR \
    --batch_size $BATCH_SIZE \
    --train_size $TRAIN_SIZE \
    --startswith "${MODEL_ID}_"
