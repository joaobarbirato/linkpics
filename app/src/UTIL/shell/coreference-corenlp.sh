#!/usr/bin/env bash
example_file=$1
output_dir=$2
java -Xmx5g -cp stanford-corenlp-3.9.2.jar:stanford-english-corenlp-models-3.9.2.jar:* \
    edu.stanford.nlp.pipeline.StanfordCoreNLP -props edu/stanford/nlp/coref/properties/deterministic-english.properties \
    -file ${example_file} -outputDirectory ${output_dir}