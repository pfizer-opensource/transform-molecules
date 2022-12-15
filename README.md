# TransformMolecules
Machine learning transformer model for generative chemistry. Code written by Emma P. Tysinger and Anton V. Sinitskiy. Paper to be published.

## Dependencies
- Install [mmpdb](https://pypi.org/project/mmpdb/) before running preparing_data.sh. For quick installation, run `pip install mmpdb`. 
- RDKit is also required for preparing_data.sh and predictions.sh. RDKit is available at http://rdkit.org/. 
- Install [OpenNMT-py](https://opennmt.net/OpenNMT-py/main.html#installation) before running training_model.sh and predictions.sh. For installation run:
 ```
git clone https://github.com/OpenNMT/OpenNMT-py.git
cd OpenNMT-py
python setup.py install
 ```
- Install [selfies](https://pypi.org/project/selfies/) before running preparing_data.sh and predictions.sh. For quick installation, run `pip install selfies`. 

## Usage
**TransformMolecules** contains 5 modules:
- Preparing Data: Generates pairs of molecules, converts molecule representation to selfies
- Dataset Split: Splits data into test/train/validation sets
- Training Model: Trains transformer model on data
- Predictions: Generate molecule predictions, converts molecule representation back to SMILES and evaluates predictions
- Generating Plots

### Preparing Data
Run the following commands:
Create a directory `$DATA_DIR` which will store all files related to the input dataset.
```
mkdir -p $DATA_DIR
```
First prepare the MMPDB input file and remove all stereochemistry and salts. The input to `./scripts/mmpdb_prep.py` (e.g., with ChEMBL data) must be a CSV file with a header (further called as /PATH/data.csv and $DATA), and at least three columns containing SMILES representation of compounds (`$SMI_COL`), ids of compounds (`$ID_COL`) and year of experimentation for the compounds (`year`). `$DATA_ID` refers to the name of the dataset.
```
python ./scripts/mmpdb_prep.py --in $DATA --out $DATA_DIR/${DATA_ID}_mmpdb_input.csv --smiles $SMI_COL --ids $ID_COL
python ./scripts/clear_stereochemistry.py --in $DATA_DIR/${DATA_ID}_mmpdb_input.csv --out $DATA_DIR/${DATA_ID}_mmpdb_input_nostereo.csv
```
Pair structurally similar molecules using MMPDB. Note that `mmpdb fragment` can take hours to run.
```
mmpdb fragment --delimiter comma --has-header $DATA_DIR/${DATA_ID}_mmpdb_input_nostereo.csv -o $DATA_DIR/${DATA_ID}.fragments
mmpdb index $DATA_DIR/${DATA_ID}.fragments -o  $DATA_DIR/${DATA_ID}_pairs.csv --out 'csv'
python ./scripts/parsing_pairs.py --in $DATA_DIR/${DATA_ID}_pairs.csv --out $DATA_DIR/${DATA_ID}_pairs_parsed.csv
```
Count the number of pairs representing each smirk, which will later be used to filter the data.
```
python ./scripts/counting_smirks.py --in $DATA_DIR/${DATA_ID}_pairs_parsed.csv --out $DATA_DIR/${DATA_ID}_counted.csv
```
Filter paired dataset by excluding all smirks with a count below a defined threshold ($EXCLUDE) and randomly sample a constant number ($SAMPLE_SIZE) from all included smirks.
```
python ./scripts/filtering_data.py --in $DATA_DIR/${DATA_ID}_pairs_parsed.csv --all $DATA --smirks $DATA_DIR/${DATA_ID}_counted.csv --out $DATA_DIR/${DATA_ID}_filtered.csv --size $SAMPLE_SIZE --exclude $EXCLUDE
```
It is strongly recommended that you submit this job to a queue using a slurm script, because it may take up to a day to complete. An example of a slurm script can be found in scripts/preparing_data.sh.
```
sbatch --export=DATA_ID=test_dataset,DATA_DIR=/PATH/test_dataset,DATA=/PATH/data.csv,SMI_COL='canonical_smiles',ID_COL='chembl_id',SAMPLE_SIZE=3,EXCLUDE=2 ./slurm_scripts/preparing_data.sh
```

### Dataset Split
Run the following commands, where `$DATA_DIR` is the directory with the paired molecules and `$RUN_DIR` is the directory to create to store all data related to a single dataset split. For year thresholds, all pairs with both molecules discovered before `$TRAIN_YEAR` will be in the training set, pairs with at least one molecule discovered later than `$TEST_YEAR` will be in the test set and all other pairs will be in the validation set. `$TIMESTAMPS` must be a CSV file with a SMILES column and a `years` column. If the `--augment` flag is used, for all pairs `(mol1, mol2)` added to the training set, the reciprocal `(mol2, mol1)` will also be added.
```
mkdir -p $RUN_DIR

## Dataset split
python ./scripts/dataset_split.py --in $DATA_DIR/${DATA_ID}_filtered.csv --timestamps $TIMESTAMPS --out $RUN_DIR --year_train $TRAIN_YEAR --year_test $TEST_YEAR --augment
```
It is strongly recommended that you submit this job to a queue using a slurm script, because it may take up to 5 hours to run. An example of a slurm script can be found in scripts/dataset_split.sh.
```
sbatch --export=DATA_ID=test_dataset,DATA_DIR=/PATH/to/paired_dataset,TIMESTAMPS=/PATH/data.csv,RUN_DIR=/PATH/to/training_dataset,TRAIN_YEAR_CUTOFF=2009,VAL_YEAR_CUTOFF=2014 ./slurm_scripts/dataset_split.sh
```

### Training Model
Install [OpenNMT-py](https://github.com/OpenNMT/OpenNMT-py) as described above (section Dependencies). 

Run the following commands:
Create a directory `$MODEL_DIR` which will store models.
```
mkdir -p $MODEL_DIR
```
Next calculate size of the training set, number of steps per epoch, number of total training steps and how often to save models based on `$BATCH_SIZE`, `$TRAIN_EPOCHS` and `$SAVE_EPOCHS`.
```
export TRAIN_SIZE=$(cat $RUN_DIR/src-train.txt | wc -l)
export EPOCH_STEPS=$(($TRAIN_SIZE/$BATCH_SIZE))
export TRAIN_STEPS=$(($EPOCH_STEPS*$TRAIN_EPOCHS))
export SAVE_STEPS=$(($EPOCH_STEPS*$SAVE_EPOCHS))
export VALID_STEPS=$(($TRAIN_STEPS+1))
```
Build the config yaml file for training parameters where `$DATA_DIR` is the directory with the paired molecules and `$RUN_DIR` is the directory storing all data related to a single dataset split.
```
cat << EOF > $DATA_DIR/config.yaml
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
```
Build vocab and start training the transformer model.
```
onmt_build_vocab -config $RUN_DIR/config.yaml -save_data $RUN_DIR/data -n_samples -1
onmt_train -config $RUN_DIR/config.yaml -save_model $MODEL_DIR/$MODEL_ID -train_steps $TRAIN_STEPS -valid_steps $VALID_STEPS -save_checkpoint_steps $SAVE_STEPS -batch_size $BATCH_SIZE -world_size 1 -gpu_ranks 0 
```
Finally rename models to be more intuitive. 
```
python ./scripts/renaming_models.py --models $MODEL_DIR --batch_size $BATCH_SIZE --train_size $TRAIN_SIZE
```
It is strongly recommended that you submit this job to a queue using a slurm script, because it may take multiple days based on the dataset size. An example of a slurm script can be found in scripts/training_model.sh.
```
sbatch --export=RUN_DIR=/PATH/to/training_dataset,MODEL_ID=test_dataset,MODEL_DIR=/PATH/model/name_of_run,TRAIN_EPOCHS=50,SAVE_EPOCHS=5,BATCH_SIZE=100
./slurm_scripts/training_model.sh
```

To resume training from a checkpoint model run the following command, where `$MODEL_PATH` is the path to the checkpoint model. 
```
onmt_train -config $RUN_DIR/config.yaml -save_model $MODEL_DIR/$MODEL_ID -train_steps $TRAIN_STEPS -valid_steps $TRAIN_STEPS -save_checkpoint_steps $SAVE_STEPS -batch_size $BATCH_SIZE -world_size 1 -gpu_ranks 0 -train_from $MODEL_PATH -reset_optim all
```

To get perplexity scores for data other than validation data, run the following command and look at the `GOLD ppl` score in the error file:
```
sbatch --export=MODEL_ID=test_dataset,MODEL_DIR=/PATH/model/name_of_run,SRC_DATA=/PATH/to/input_dataset,TGT_DATA=/PATH/to/true_dataset,EPOCH_NUM=10,OUTPUT_DIR=/PATH/to/predictions ./slurm_scripts/model_scoring.sh
```

### Predictions
Run the following commands:
Create a txt file with all unique validation molecules and generate new structure predictions with the validation molecules as input to a trained model with `$MODEL_ID` and at `$EPOCH_NUM`. `$RUN_DIR` is the directory storing all data related to a single dataset split, `$MODEL_DIR` is the directory storing the trained model and `$OUTPUT_DIR` is the directory where predictions will be saved.
```
mkdir -p $OUTPUT_DIR
cat $RUN_DIR/src-val.txt $RUN_DIR/tgt-val.txt | sort | uniq > $RUN_DIR/val-unique.txt
if [ ! -s $OUTPUT_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt ]; then
    onmt_translate --model $MODEL_DIR/${MODEL_ID}_epoch_${EPOCH_NUM}.pt --src $RUN_DIR/val-unique.txt --output $OUTPUT_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt --replace_unk --seed 1 --gpu 0
fi
```
Convert SELFIEs of generated molecules to SMILES and get scaffolds of all input validation and generated molecules.
```
python ./scripts/selfies_to_smiles.py --in1 $RUN_DIR/pred_selfies_epoch_${EPOCH_NUM}.txt --in2 $RUN_DIR/src-val-unique.txt --out $RUN_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv
python ./scripts/scaffolding.py --in $RUN_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv --out $RUN_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv --column1 'structure' --column2 'id'
```
Score generated molecules based on number of scaffold changes, number of r-group changes, number of unique scaffolds and number of new scaffolds. `$METRICS_TABLE` is the csv file where scores will be added. If csv doesn't exist yet, one will be created. 
```
## Score model predictions
python ./scripts/scoring.py --in $RUN_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv --metrics_table $METRICS_TABLE --training_data $RUN_DIR/train.csv --model ${MODEL_ID}_epoch_${EPOCH_NUM} --change_count --scaffolds
```
It is strongly recommended that you submit this job to a queue using a slurm script, because it may take up to 1 day based on the dataset size. An example of a slurm script can be found in scripts/predictions.sh.
```
sbatch --export=RUN_DIR=/PATH/to/training_dataset,MODEL_ID=test_dataset,MODEL_DIR=MODEL_DIR=/PATH/model/name_of_run,OUTPUT_DIR=/PATH/to/predictions,EPOCH_NUM=10,METRICS_TABLE=/PATH/model_scores.csv ./slurm_scripts/predictions.sh
```

An additional slurm script can be run to determine the new smirks predicted by the model by running the following command, where `$THRESHOLD` is the threshold of smirks count above which pngs of smirks will be created and `$PNG_DEST` is an existant directory or one that will be created to save SMIRK pngs to.
```
sbatch --export=EPOCH_NUM=10,OUTPUT_DIR=/PATH/to/predictions,DATA_DIR=/PATH/to/paired_dataset,DATA_ID=test_dataset,THRESHOLD=2,PNG_DEST=/DIRECTORY/for/pngs ./slurm_scripts/new_smirks.sh
```

### Generating Plots
#### **Scaffolding scores**
To generate line plots for scaffold scores over multiple epochs run the following command. Specify which runs in the metrics_table.csv to plot with `$SUBSET` which is a string identifier in the model names.
```
mkdir -p $PLOT_DIR
python ./scripts/generating_plots.py --metrics_table $METRICS_TABLE --out $PLOT_DIR --subset $SUBSET, --type scores
```
#### **Molecular Property Histograms**
To generate histogram plots comparing molecular properties of generated molecules compared to the input molecules of the model for training, first get the molecular properties of generated and input molecules with the following commands:
```
python ./scripts/molecular_properties.py --in $DATA_DIR/${DATA_ID}_mmpdb_input_nostereo.csv --out $DATA_DIR/${DATA_ID}_molecular_properties.csv --smi_col $SMI_COL  
python ./scripts/molecular_properties.py --in $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv --out $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv \--smi_col 'structure'
```
Next, to generate the histograms run the following command:
```
mkdir -p $PLOT_DIR
python ./scripts/generating_plots.py --in1 $OUTPUT_DIR/pred_smiles_epoch_${EPOCH_NUM}.csv --in2 $DATA_DIR/${DATA_ID}_molecular_properties.csv --out $PLOT_DIR --type molecular_properties
```
#### **Training Curves and Scaffolding Scores**
To generate stacks plots with perplexity and scaffolding scores first parse the training log and info files to generate csv files with perplexity and accuracy scores. `$IN_FILE` is a txt file with information about the model including the split name and filter used, and `$OUTDEST` is the name of the directory to save all files generated for this script. 
```
mkdir -p $OUTDEST
python ./scripts/training_curves.py --in $IN_FILE --out $OUTDEST/training_model_info_${MODEL_NUM}.csv --parse_type info

export NAME=validation_accuracy
grep 'Validation accuracy' $ERR_FILE > $OUTDEST/${NAME}_${MODEL_NUM}.err
python ./scripts/training_curves.py --in $OUTDEST/${NAME}_${MODEL_NUM}.err --out $OUTDEST/${NAME}_${MODEL_NUM}.csv --name $NAME --parse_type val
    
export NAME=validation_perplexity
grep 'Validation perplexity' $ERR_FILE > $OUTDEST/${NAME}_${MODEL_NUM}.err
python ./scripts/training_curves.py --in $OUTDEST/${NAME}_${MODEL_NUM}.err --out $OUTDEST/${NAME}_${MODEL_NUM}.csv --name $NAME --parse_type val
 
export NAME=training
grep 'Start training loop and validate' $ERR_FILE > $OUTDEST/${NAME}_${MODEL_NUM}.err
grep 'acc:' $ERR_FILE >> $OUTDEST/${NAME}_${MODEL_NUM}.err
python ./scripts/training_curves.py --in $OUTDEST/${NAME}_${MODEL_NUM}.err --out $OUTDEST/${NAME}_${MODEL_NUM}.csv --name $NAME --outpng $OUTDEST --parse_type train
```
Finally run the following command to generate the stacked plots. Make sure the `$METRICS_TABLE` csv file contained the scores for the split and filter being used. 
```
mkdir -p $PLOTDEST
python /gpfs/workspace/users/tysine/Transformer/training_curves.py --val_acc $OUTDEST/validation_accuracy_${MODEL_NUM}.csv --val_ppl $OUTDEST/validation_perplexity_${MODEL_NUM}.csv --train $OUTDEST/training_${MODEL_NUM}.csv --info $OUTDEST/training_model_info_${MODEL_NUM}.csv --metrics $METRICS_TABLE --outpng $PLOTDEST --epoch_cutoff $EPOCH_CUTOFF --parse_type plot
```
The following slurm script can be run to automate all these steps, where `$MODEL_NUM` is the job id when training the model:
```
sbatch --export=$IN_FILE=/PATH/to/model_info.txt,ERR_FILE=/PATH/to/training_log.txt,OUTDEST=/PATH/to/output_directory,MODEL_NUM=model_num,METRICS_TABLE=/PATH/to/metrics.csv,PLOTDEST=directory_to_save_plots,EPOCH_CUTOFF=32 ./slurm_scripts/training_curves.sh
```

### Held-Out Target-Specific Data
Scripts related to filtering datasets for target-specific data require a dataset of molecules with a column `tid` refering to the target id of the molecule's target as well as another dataset (refered to as `\PATH\to\target_id_dataset`) mapping target id's (`tid`) to their chembl_id. This target_id_dataset can be downloaded from `chembl_dataset.zip` and is titled `target_information.csv`. To generate the datasets with no target-specific data run the filtering scripts with additional inputs including the name of the target (`$TARGET`):
```
python ./scripts/filtering_data.py --in $DATA_DIR/${DATA_ID}_pairs_parsed.csv --all $DATA --smirks $DATA_DIR/${DATA_ID}_counted.csv --out $DATA_DIR/${DATA_ID}_filtered_${TARGET}.csv --size $SAMPLE_SIZE --exclude $EXCLUDE --target 'target chembl_id' --tid \PATH\to\target_id_dataset
```
Run the **Dataset Split** and **Training Model** modules to same as described earlier with `$DATA_DIR/${DATA_ID}_filtered_${TARGET}.csv`. Next split the target-specific data temporally and by activity. 

To generate images for the experimental molecules for a specific target, the most similar generated molecule(calculated with Tanimoto similarity) and the input molecule for given generated molecule run the following command, where `$SMI_COL` is the name of the column with SMILEs representations in `--in1` and `$PNG_DEST` is an existant directory or one that will be created to save molecule pngs to. 
```
python ./scripts/tanimoto_target_specific.py --in1 /PATH/to/target_molecules --in2 /PATH/to/generated_molecules --smi_col $SMI_COL --out $OUTPUT_DIR/top_generated_per_experimental.csv --png_dest $PNG_DEST --generate_png
```

