#!/usr/bin/env bash

## 1.
## Setup TreeTagger
base_dir=$(pwd)
tree_tagger_dir="./TreeTagger"
echo $tree_tagger_dir
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
mkdir $tree_tagger_dir
mv tree-tagger-linux-3.2.2.tar.gz $tree_tagger_dir
cd $tree_tagger_dir
tar xvzf tree-tagger-linux-3.2.2.tar.gz

wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
tar xvzf tagger-scripts.tar.gz

wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh

wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz
gunzip english.par.gz

rm *.tar.gz

cd ..

mv $tree_tagger_dir app/src/PLN

cd app/src/PLN/$tree_tagger_dir

sh install-tagger.sh

cd $base_dir

# 2.
# Installing git dependencies
pip install git+https://github.com/miotto/treetagger-python/
pip install dlib==19.13.1

# 3. Downloading YOLO
git clone https://github.com/pjreddie/darknet
cd darknet
make
wget https://pjreddie.com/media/files/yolov3.weights
./darknet detect cfg/yolov3.cfg yolov3.weights data/dog.jp
cd ..
mv darknet app/src/IA/YOLO
cd $base_dir
