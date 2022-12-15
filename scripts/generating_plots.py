import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse 

def molecular_properties_hist(args):
    labels = {'mol_wt':'Molecular Weights', 'h_donors':'Hydrogen Bond Donors', 'h_acceptors':'Hydrogen Bond Acceptors', 'mol_logp':'Octanol-Water Partition Coefficients'}
    generated_df = pd.read_csv(args.infile1)
    generated_df['molwt_diff'] = (generated_df['mol_wt_structure'] - generated_df['mol_wt_id'])
    generated_df['logp_diff'] = (generated_df['mol_logp_structure'] - generated_df['mol_logp_id'])
    all_df = pd.read_csv(args.infile2)
    
    fig, ((ax1, ax2,ax5), (ax3, ax4,ax6)) = plt.subplots(2, 3, figsize=(16, 8))
    x='mol_wt'
    n, bins, patches = ax2.hist([generated_df[f"{x}_structure"],generated_df[f"{x}_id"]], bins = 30, histtype='step', density=True)
    ax2.set_xlabel(labels[x])
    x='h_donors'
    n, bins, patches = ax1.hist([generated_df[f"{x}_structure"],generated_df[f"{x}_id"]], bins = 14, histtype='step', density=True)
    ax1.set_xlabel(labels[x])
    x='h_acceptors'
    n, bins, patches = ax3.hist([generated_df[f"{x}_structure"],generated_df[f"{x}_id"]], bins = 20, histtype='step', density=True)
    ax3.set_xlabel(labels[x])
    ax3.set_xticks([2,4,6,8,10,12,14,16])
    x='mol_logp'
    n, bins, patches = ax4.hist([generated_df[f"{x}_structure"],generated_df[f"{x}_id"]], bins = 30, histtype='step', density=True)
    ax4.set_xlabel(labels[x])
    
    n, bins, patches = ax5.hist(generated_df['molwt_diff'], bins = 30, histtype='step')
    ax5.set_xlabel('Molecular Weight Differences')
    
    n, bins, patches = ax6.hist(generated_df['logp_diff'], bins = 30, histtype='step')
    ax6.set_xlabel('Octanol-Water Partition Coefficient Differences')
    
    fig.suptitle(f'Molecular Properties Distributions Comparison Generated vs. Input',fontsize=15)
    ax1.legend(labels=['Generated Molecules', 'Input Molecules'])
    plt.savefig(f"{args.outdest}/generated_input_plot.png")
    
    plt.clf()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    x='mol_wt'
    n, bins, patches = ax2.hist([generated_df[f"{x}_structure"],all_df[f"{x}_{args.smi_col}"]], bins = 30, histtype='step', density=True)
    ax2.set_xlabel(labels[x])
    x='h_donors'
    n, bins, patches = ax1.hist([generated_df[f"{x}_structure"],all_df[f"{x}_{args.smi_col}"]], bins = 15, histtype='step', density=True)
    ax1.set_xlabel(labels[x])
    ax1.set_xticks([2,4,6,8,10,12,14])
    x='h_acceptors'
    n, bins, patches = ax3.hist([generated_df[f"{x}_structure"],all_df[f"{x}_{args.smi_col}"]], bins = 30, histtype='step', density=True)
    ax3.set_xlabel(labels[x])
    x='mol_logp'
    n, bins, patches = ax3.hist([generated_df[f"{x}_structure"],all_df[f"{x}_{args.smi_col}"]], bins = 30, histtype='step', density=True)
    ax3.set_xlabel(labels[x])
    
    fig.suptitle(f'Molecular Properties Distributions Comparison Generated vs. CHEMBL',fontsize=15)
    ax1.legend(labels=['Generated Molecules', 'CHEMBL Molecules'])
    plt.savefig(f"{args.outdest}/generated_chembl_plot.png")
    

def scores_lineplot(args):
    models_df = pd.read_csv(args.metrics_table)
    models_df = models_df.set_index('model')
    models_df.sort_values(by=['model_name','epoch'],inplace=True)

    plot_save_dict = {'Count':'count', 'Scaffold Change Count':'scaffold_change_count', 'R-Group Change Count':'r_group_change_count', 'Unique Scaffolds':'unique_scaffolds', 'New Scaffolds':'new_scaffolds'}

    models = list(set(models_df[models_df.model_name.notna()]['model_name']))
    models.sort()
        
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, sharex='col', figsize=(18, 8))
    y = 'Count'
    for x in [n for n in models if (type(n)==str) and (args.subset in n)]:
        ax3.plot(models_df[(models_df.model_name == x)&(models_df[y] != 0)]['epoch'], models_df[(models_df.model_name == x)&(models_df[y] != 0)][y], label = 'pre-triage')
    ax3.set_ylabel(y)
    ax6.set_xlabel('Epoch Number')
    ax3.tick_params(axis='y', which='major', labelsize=8)
    
    y = 'Scaffold Change Count'
    for x in [n for n in models if (type(n)==str) and (args.subset in n)]:
        ax2.plot(models_df[(models_df.model_name == x)&(models_df[y] != 0)]['epoch'], models_df[(models_df.model_name == x)&(models_df[y] != 0)][y], label = 'pre-triage')
    ax2.set_ylabel(y)
    ax2.tick_params(axis='y', which='major', labelsize=8)
        
    y = 'R-Group Change Count'
    for x in [n for n in models if (type(n)==str) and (args.subset in n)]:
        ax5.plot(models_df[(models_df.model_name == x)&(models_df[y] != 0)]['epoch'], models_df[(models_df.model_name == x)&(models_df[y] != 0)][y], label = 'pre-triage')
    ax5.set_ylabel(y)
    ax5.set_xlabel('Epoch Number')
    ax5.tick_params(axis='y', which='major', labelsize=8)
    
    y = 'Unique Scaffolds'
    for x in [n for n in models if (type(n)==str) and (args.subset in n)]:
        ax4.plot(models_df[(models_df.model_name == x)&(models_df[y] != 0)]['epoch'], models_df[(models_df.model_name == x)&(models_df[y] != 0)][y], label = 'pre-triage')
    ax4.set_ylabel(y) 
    ax4.set_xlabel('Epoch Number')
    ax4.tick_params(axis='y', which='major', labelsize=8)
    
    y = 'New Scaffolds'
    for x in [n for n in models if (type(n)==str) and (args.subset in n)]:
        ax1.plot(models_df[(models_df.model_name == x)&(models_df[y] != 0)]['epoch'], models_df[(models_df.model_name == x)&(models_df[y] != 0)][y], label = 'pre-triage')
    ax1.set_ylabel(y)
    ax1.tick_params(axis='y', which='major', labelsize=8)
    
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.subplots_adjust(hspace=.0)
    # remove last tick label for the second subplot
    #yticks = ax2.yaxis.get_major_ticks()
    #yticks[-1].label1.set_visible(False)
    fig.suptitle(f"Chemical scores for {args.subset}", fontsize=16)
    plt.savefig(f"{args.outdest}/{args.subset}_chemical_scores.png")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics_table", dest="metrics_table", help="File with metrics", metavar="in.csv")
    parser.add_argument("--in1", dest='infile1', help="csv file containing molecular properties of generated and input molecules", metavar="in1.csv")
    parser.add_argument("--in2", dest='infile2', help="csv file containing molecular properties of training molecules", metavar="in2.csv")
    parser.add_argument("--out", dest="outdest", help="output destination", metavar="input.txt")
    parser.add_argument("--subset", dest="subset", help="model name containing subset string will be used")
    parser.add_argument("--type", dest="plot_type", help="type of plot to generate")
    parser.add_argument("--smi_col", dest="smi_col", help="name of smiles column in infile2")
    args = parser.parse_args()
    
    if args.plot_type == 'scores':
        scores_lineplot(args)
    elif args.plot_type == 'molecular_properties':
        molecular_properties_hist(args)

if __name__=='__main__':
    main()
