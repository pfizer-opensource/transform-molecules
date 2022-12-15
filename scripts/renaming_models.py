import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Rename .pt files for trained models: replace numbers of steps by numbers of epochs.")
    parser.add_argument("--models", dest="models", help="model directory")
    parser.add_argument("--batch_size", dest="batch_size", help="batch size")
    parser.add_argument("--train_size", dest="train_size", help="training data size")
    parser.add_argument("--startswith", dest="startswith", help="only .pt files with names starting with this string will be renamed", default="")
    args = parser.parse_args()
    
    epoch_steps = round(int(args.train_size)/int(args.batch_size))
    
    for model in os.listdir(args.models):
        if model.startswith(args.startswith):
            if '_step_' in model:
                prefix, suffix = model.split('_step_')
                step_num = int(suffix[:-3])
                epoch_num = round(step_num/epoch_steps)
                os.rename(f"{args.models}/{model}", f"{args.models}/{prefix}_epoch_{epoch_num}.pt")

if __name__=='__main__':
    main()
