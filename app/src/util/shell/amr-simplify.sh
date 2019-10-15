#!/usr/bin/env bash

base_dir=$1
simplifier_path=${base_dir}/app/src/amr/neural-graph-to-seq-mp/amr_simplifier

cd ${simplifier_path}

./anonDeAnon_java.sh anonymizeAmrFull true $2

cd ${base_dir}
