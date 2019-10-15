#!/usr/bin/env bash

base_dir=$1
g2s_path=${base_dir}/app/src/amr/neural-graph-to-seq-mp

touch $2.anonymized

cd ${g2s_path}

export PATH=${g2s_path}:$PATH/g2s/bin
export VIRTUAL_ENV=${g2s_path}/g2s
export CUDA_VISIBLE_DEVICES=0
source ${g2s_path}/g2s/bin/activate

export PYTHONPATH=$(pwd):$PYTHONPATH

python src_g2s/G2S_beam_decoder.py --model_prefix logs_g2s/G2S.silver_2m \
        --in_path $2 \
        --out_path $2.tok \
        --mode beam

cd ${base_dir}
