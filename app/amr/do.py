from src.train import read_dicts,train_parser
from src.parse import generate_parser
from parser.AMRProcessors import *
from torch import cuda

# python do.py -train_from scratch/s1544871/model/gpus_0valid_best.pt -input input.txt

def parse_amr_txt():
    global opt
    opt = generate_parser().parse_args()
    opt.lemma_dim = opt.dim
    opt.high_dim = opt.dim

    opt.cuda = None
    opt.gpus[0] = -1

    # if opt.cuda and opt.gpus[0] != -1:
    #     cuda.set_device(opt.gpus[0])
    dicts = read_dicts()

    Parser = AMRParser(opt,dicts)
    if opt.input:
        filepath = opt.input
        out = opt.output if opt.output else filepath+"_parsed"
        print ("processing "+filepath)
        n = 0
        with open(out,'w') as out_f:
            with open(filepath,'r') as f:
                line = f.readline()
                while line != '' :
                    if line.strip() != "":
                        output = Parser.parse_batch([line.strip()])
                        out_f.write("# ::snt "+line)
                        out_f.write(output[0])
                        out_f.write("\n")
                    line = f.readline()
        print ("done processing "+filepath)
        print (out +" is generated")
    elif opt.text:
        output = Parser.parse_one(opt.text)
        print ("# ::snt "+opt.text)
        for i in output:
            print (i)
    else:
        print ("option -input [file] or -text [sentence] is required.")

if __name__ == "__main__":
    parse_amr_txt()
