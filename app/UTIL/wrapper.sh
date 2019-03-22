#!/bin/bash
cd amr
python do.py -train_from scratch/s1544871/model/gpus_0valid_best.pt -input input.txt
cd ..