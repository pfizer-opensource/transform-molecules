import pandas as pd
import numpy as np
import argparse
from os import path

def change_count(args):
    inf = pd.read_csv(args.infile)
    inf['change_type'] = ['same' if inf.loc[n]['id_canonical'] == inf.loc[n]['structure_canonical'] else 'r-group' if inf.loc[n]['id_scaffold'] == inf.loc[n]['structure_scaffold'] else 'scaffold' for n in range(inf.shape[0])]
    metrics = pd.read_csv(args.metrics)
    metrics = metrics.set_index('model')
    
    metrics.loc[args.model,'Count'] = inf.shape[0]
    metrics.loc[args.model,'Scaffold Change Count'] = inf[inf['change_type'] == 'scaffold'].shape[0]
    metrics.loc[args.model,'R-Group Change Count'] = inf[inf['change_type'] == 'r-group'].shape[0]
    metrics.to_csv(args.metrics)

def scaffolds(args):
    inf = pd.read_csv(args.infile)
    train = pd.read_csv(args.training_data, header=None)
    metrics = pd.read_csv(args.metrics)
    metrics = metrics.set_index('model')
    
    metrics.loc[args.model,'Unique Scaffolds'] = len(set(inf['structure_scaffold']))
    metrics.loc[args.model,'Validation Scaffolds'] = len(set(inf['id_scaffold']))
    metrics.loc[args.model,'New Scaffolds'] = len(set(inf['structure_scaffold']).difference(*[set(inf['id_scaffold']), set(train[6]), set(train[7])])) 
    metrics.loc[args.model,'Training Scaffolds'] = len(set(train[6]).union(set(train[7])))
    metrics.to_csv(args.metrics)

def main():
    parser = argparse.ArgumentParser(description="Calculate chemical scores of generated molecules from a model")
    parser.add_argument("--in", dest="infile", help="csv input file of original and predicted smiles, and scaffolds", metavar="input.txt")
    parser.add_argument("--metrics_table", dest="metrics", help="File with metrics so far", metavar="metrics.csv")
    parser.add_argument("--training_data", dest="training_data", help="Training dataset file", metavar="train.csv")
    parser.add_argument("--model", dest="model", help="name of model")
    parser.add_argument("--change_count", dest="change_count", action='store_true')
    parser.add_argument("--scaffolds", dest="scaffolds", action='store_true')
    args = parser.parse_args()
    
    if not path.isfile(args.metrics):
        metrics_df = pd.DataFrame(columns=["model","Count","Scaffold Change Count","R-Group Change Count","Unique Scaffolds","New Scaffolds","Validation Scaffolds","Training Scaffolds"])
        metrics_df = metrics_df.set_index('model')
        metrics_df.to_csv(args.metrics)
        
    metrics_df = pd.read_csv(args.metrics)
    metrics_df = metrics_df.set_index('model')
    if args.model not in metrics_df.index.values.tolist():
        metrics_df = metrics_df.reindex(metrics_df.index.values.tolist() + [args.model])
    model_id, epoch = tuple(args.model.split('_epoch_'))
    metrics_df.loc[args.model,'model_name'] = model_id
    metrics_df.loc[args.model,'epoch'] = int(epoch)
    metrics_df.to_csv(args.metrics)
    del metrics_df

    if args.change_count:
        change_count(args)

    if args.scaffolds:
        scaffolds(args)             
    
if __name__=='__main__':
    main()
