 #!/bin/bash --login
#SBATCH -o .../model_scoring.sh.out
#SBATCH -e .../model_scoring.sh.err
#SBATCH -n 1
#SBATCH -t 4:00:00
#SBATCH --mem-per-cpu=50G
#SBATCH --gres=gpu:1

#export PYTHONPATH=...
export CUDA_VISIBLE_DEVICES=0

mkdir -p $OUTPUT_DIR
 
onmt_translate \
    --model $MODEL_DIR/${MODEL_ID}_epoch_${EPOCH_NUM}.pt \
    --src $SRC_DATA \
    --tgt $TGT_DATA \
    --output $OUTPUT_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt \
    --replace_unk \
    --seed 1 \
    --gpu 0
