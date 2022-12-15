import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import math

def parsed_info(args):
    with open(args.infile, 'r') as ifs:
        with open(args.outfile, 'w') as ofs:
            ofs.write(f'Job ID,Train Year,Test Year,Batch Size,Filter\n')
            for line in ifs:
                parsed = line.strip().split('ID ')[1]
                job_id = int(parsed.split(' ')[0])
                parsed = parsed.split(' ')
                train_year = int(parsed[1].split('=')[1])
                test_year = int(parsed[2].split('=')[1])
                batch = int(parsed[3].split('=')[1])
                filtered = int(parsed[4].split('=')[1])
                ofs.write(f"{job_id},{train_year},{test_year},{batch},{filtered}\n")

def parsed_val(args):
    col_dict = {'validation_accuracy':'Validation accuracy','validation_perplexity':'Validation perplexity'}

    with open(args.infile, 'r') as ifs:
        with open(args.outfile, 'w') as ofs:
            ofs.write(f'Time,Epoch,{col_dict[args.name]}\n')
            n=1
            for line in ifs:
                parsed = line.strip().split(': ')
                ofs.write(f"{parsed[0]},{n},{parsed[1]}\n")
                n+=1

def parsed_training(args):
    with open(args.infile, 'r') as ifs:
        with open(args.outfile,'w') as ofs:
            ofs.write(f'Time,Step,Accuracy,Perplexity\n')
            n=0
            for line in ifs:
                if n==0:
                    epoch_steps = int(line.strip().split(' every ')[1].split(' steps')[0])
                    n=1
                elif n==1:
                    parsed = line.strip().split('; ')
                    time = parsed[0].split('] ')[0]+']'
                    try:
                        step = parsed[0].split(' Step ')[1].split('/')[0]
                    except IndexError:
                        print(line)
                    #print(parsed[0].split(' Step ')[1])
                    acc = float(parsed[1][5:])
                    ppl = float(parsed[2][5:])
                    ofs.write(f"{time},{step},{acc},{ppl}\n")
    scores_df = pd.read_csv(args.outfile)
    scores_df['Epoch'] = scores_df['Step'].apply(lambda x: math.ceil(x/epoch_steps))
    epoch_scores = scores_df.groupby('Epoch')['Accuracy','Perplexity'].mean()
    epoch_scores.to_csv(args.outfile)
    return epoch_steps

def plots(args, triaged=False):
    info = pd.read_csv(args.info)
    val_acc_df = pd.read_csv(args.val_acc)
    val_ppl_df = pd.read_csv(args.val_ppl)
    val_acc_df.reset_index(inplace=True)
    val_ppl_df.reset_index(inplace=True)
    train_df = pd.read_csv(args.train)
    models_df = pd.read_csv(args.metrics)
    subset = f"split{info.loc[0,'Train Year']}_{info.loc[0,'Test Year']}_filter{info.loc[0,'Filter']}"
    models = list(set(models_df[models_df.model_name.notna()]['model_name']))
    models.sort()
    if triaged:
        triaged_df = pd.read_csv(args.triaged)
        triaged_models = list(set(triaged_df[triaged_df.model_name.notna()]['model_name']))
        triaged_models.sort()

    fig, ((ax2), (ax3), (ax4), (ax5), (ax6)) = plt.subplots(5, 1, sharex='col',figsize=(10, 16))
    plt.rcParams.update({'legend.fontsize': 'x-large'})
    ax2.tick_params(axis='y', which='major', labelsize='x-large')
    ax3.tick_params(axis='y', which='major', labelsize='x-large')
    ax4.tick_params(axis='y', which='major', labelsize='x-large')
    ax5.tick_params(axis='y', which='major', labelsize='x-large')
    ax6.tick_params(which='major', labelsize='x-large')

    ax2.plot(train_df[train_df['Epoch']<=int(args.epoch_cutoff)]['Epoch'],train_df[train_df['Epoch']<=int(args.epoch_cutoff)]['Perplexity'], label='Perplexity (Train)', color='blue')
    ax2.plot(val_ppl_df[val_ppl_df['Epoch']<=int(args.epoch_cutoff)]['Epoch'],val_ppl_df[val_ppl_df['Epoch']<=int(args.epoch_cutoff)]['Validation perplexity'], label='Perplexity (Validation)', color='red')
    ax2.set_ylim([0, 3])
    ax2.set_yticks([0,1,2,3])

    ppl_diff = [val_ppl_df.loc[n,'Validation perplexity'] - train_df.loc[n,'Perplexity'] for n in range(val_ppl_df.shape[0])]
    ppl_change = [val_ppl_df.loc[n,'Validation perplexity'] - val_ppl_df.loc[n-1,'Validation perplexity'] if n>0 else 0 for n in range(val_ppl_df.shape[0])]
    zipped = zip(ppl_diff, val_ppl_df['Epoch'], ppl_change)
    zipped = [x for x in zipped if x[1]<=int(args.epoch_cutoff)]
    unzipped = res = [[ i for i, j, k in zipped],[ j for i, j, k in zipped], [ k for i, j, k in zipped]]
    ax3.plot(unzipped[1],unzipped[0], label='Perplexity Validation - Train')
    ax3.plot(unzipped[1],unzipped[2], label='Delta Perplexity Validation')
    ax3.set_ylim([-1, 1])
    ax3.set_yticks([-0.5, 0, 0.5])

    y = 'Count'
    for x in [n for n in models if (type(n)==str) and (subset==n)]:
        mask = (models_df.model_name == x)&(models_df[y] != 0)&(models_df.epoch<=int(args.epoch_cutoff))
        df_current = models_df[mask][['epoch',y]]
        df_current.sort_values(by='epoch', inplace=True)
        ax4.plot(df_current['epoch'], df_current[y], label = y, color='indigo')
    if triaged:
        for x in [n for n in triaged_models if (type(n)==str) and (subset==n)]:
            mask = (triaged_df.model_name == x)&(triaged_df[y] != 0)&(triaged_df.epoch<=int(args.epoch_cutoff))
            df_current = triaged_df[mask][['epoch',y]]
            df_current.sort_values(by='epoch', inplace=True)
            ax4.plot(df_current['epoch'], df_current[y], label = f'Post-triage {y}', color='orchid')

    y = 'Scaffold Change Count'
    for x in [n for n in models if (type(n)==str) and (subset==n)]:
        mask = (models_df.model_name == x)&(models_df[y] != 0)&(models_df.epoch<=int(args.epoch_cutoff))
        df_current = models_df[mask][['epoch',y]]
        df_current.sort_values(by='epoch', inplace=True)
        ax4.plot(df_current['epoch'], df_current[y], label = y, color='forestgreen')
    if triaged:
        for x in [n for n in triaged_models if (type(n)==str) and (subset==n)]:
            mask = (triaged_df.model_name == x)&(triaged_df[y] != 0)&(triaged_df.epoch<=int(args.epoch_cutoff))
            df_current = triaged_df[mask][['epoch',y]]
            df_current.sort_values(by='epoch', inplace=True)
            ax4.plot(df_current['epoch'], df_current[y], label = f'Post-triage {y}', color='lightgreen')

    y = 'R-Group Change Count'
    for x in [n for n in models if (type(n)==str) and (subset==n)]:
        mask = (models_df.model_name == x)&(models_df[y] != 0)&(models_df.epoch<=int(args.epoch_cutoff))
        df_current = models_df[mask][['epoch',y]]
        df_current.sort_values(by='epoch', inplace=True)
        ax5.plot(df_current['epoch'], df_current[y], label = y, color='black')
    if triaged:
        for x in [n for n in triaged_models if (type(n)==str) and (subset==n)]:
            mask = (triaged_df.model_name == x)&(triaged_df[y] != 0)&(triaged_df.epoch<=int(args.epoch_cutoff))
            df_current = triaged_df[mask][['epoch',y]]
            df_current.sort_values(by='epoch', inplace=True)
            ax5.plot(df_current['epoch'], df_current[y], label = f'Post-triage {y}', color='gray')

    y = 'Unique Scaffolds'
    for x in [n for n in models if (type(n)==str) and (subset==n)]:
        mask = (models_df.model_name == x)&(models_df[y] != 0)&(models_df.epoch<=int(args.epoch_cutoff))
        df_current = models_df[mask][['epoch',y]]
        df_current.sort_values(by='epoch', inplace=True)
        ax6.plot(df_current['epoch'], df_current[y], label = y, color='darkred')
    if triaged:
        for x in [n for n in triaged_models if (type(n)==str) and (subset==n)]:
            mask = (triaged_df.model_name == x)&(triaged_df[y] != 0)&(triaged_df.epoch<=int(args.epoch_cutoff))
            df_current = triaged_df[mask][['epoch',y]]
            df_current.sort_values(by='epoch', inplace=True)
            ax6.plot(df_current['epoch'], df_current[y], label = f'Post-triage {y}', color='lightcoral')

    y = 'New Scaffolds'
    for x in [n for n in models if (type(n)==str) and (subset==n)]:
        mask = (models_df.model_name == x)&(models_df[y] != 0)&(models_df.epoch<=int(args.epoch_cutoff))
        df_current = models_df[mask][['epoch',y]]
        df_current.sort_values(by='epoch', inplace=True)
        ax6.plot(df_current['epoch'], df_current[y], label = y, color='magenta')
    if triaged:
        for x in [n for n in triaged_models if (type(n)==str) and (subset==n)]:
            mask = (triaged_df.model_name == x)&(triaged_df[y] != 0)&(triaged_df.epoch<=int(args.epoch_cutoff))
            df_current = triaged_df[mask][['epoch',y]]
            df_current.sort_values(by='epoch', inplace=True)
            ax6.plot(df_current['epoch'], df_current[y], label = f'Post-triage {y}', color='violet')

    # put legends on subplots
    ax2.legend()
    ax3.legend()
    ax4.legend(loc='lower right')
    ax5.legend(loc='lower right')
    ax6.legend(loc='lower right')

    # remove vertical gap between subplots
    plt.subplots_adjust(hspace=.0)

    ax6.set_xlabel('Epoch Number', fontsize='x-large')
    suffix = '' if triaged else '_manuscript'
    plt.savefig(f"{args.outpng}/split{info.loc[0,'Train Year']}_{info.loc[0,'Test Year']}_filter{info.loc[0,'Filter']}_batch{info.loc[0,'Batch Size']}{suffix}.png")

def main():
    parser = argparse.ArgumentParser(description="Make training Curves for trained models")
    parser.add_argument("--in", dest="infile", help="err or out txt file from training", metavar="input.txt")
    parser.add_argument("--out", dest="outfile", help="output file", metavar="output.csv")
    parser.add_argument("--info", dest="info", help="CSV with run info", metavar='info.csv')
    parser.add_argument("--name", dest="name", help="Name training/validation metric")
    parser.add_argument("--outpng", dest="outpng", help="plot png destination")
    parser.add_argument("--parse_type", dest="parse_type")
    parser.add_argument("--val_acc", dest="val_acc", help="CSV with validation accuracy scores", metavar="val_acc.csv")
    parser.add_argument("--val_ppl", dest="val_ppl", help="CSV with validation perplexity scores", metavar="val_ppl.csv")
    parser.add_argument("--train", dest="train", help="CSV with training scores", metavar="train.csv")
    parser.add_argument("--metrics", dest="metrics", help="CSV with chemical scores", metavar="metrics.csv")
    parser.add_argument("--triaged", dest="triaged", help="CSV with chemical scores of triaged molecules", metavar="triaged.csv")
    parser.add_argument("--epoch_cutoff", dest="epoch_cutoff", help="epoch cutoff to graph up until", default=32)
    args = parser.parse_args()

    if args.parse_type == 'info':
        parsed_info(args)
    elif args.parse_type == 'val':
        parsed_val(args)
    elif args.parse_type == 'train':
        epoch_steps = parsed_training(args)
    elif args.parse_type == 'plot':
        plots(args)
    elif args.parse_type == 'plot_w_triaged':
        plots(args, triaged=True)


if __name__=='__main__':
    main()
