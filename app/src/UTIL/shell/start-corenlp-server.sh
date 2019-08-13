#!/usr/bin/env sh
FIRST_DIR=$(pwd)
cd $1
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000 &
PID=$!
cd $FIRST_DIR
echo $! > $2/serverpid.txt