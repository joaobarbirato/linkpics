#!/usr/bin/env bash
FIRST_DIR=$(pwd)
working_dir=$1
example_file=$2
output_dir=$3
cd $1
java -Xmx5g -cp stanford-corenlp-3.9.2.jar:stanford-english-corenlp-models-3.9.2.jar:* \
    edu.stanford.nlp.pipeline.StanfordCoreNLP -props edu/stanford/nlp/coref/properties/deterministic-english.properties \
    -file ${example_file} -outputDirectory ${output_dir}
cd ${FIRST_DIR}