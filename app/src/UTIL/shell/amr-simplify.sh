#!/usr/bin/env bash

base_dir=$(pwd)
simplifier_path=${base_dir}/app/src/amr/neural-graph-to-seq-mp/amr_simplifier

cd ${simplifier_path}

./anonDeAnon_java.sh anonymizeAmrFull true $1

cd ${base_dir}
