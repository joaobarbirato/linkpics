#!/usr/bin/env bash

## 1.
## Setup TreeTagger
base_dir=$(pwd)
tree_tagger_dir="./TreeTagger"
echo ${tree_tagger_dir}
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
mkdir ${tree_tagger_dir}
mv tree-tagger-linux-3.2.2.tar.gz ${tree_tagger_dir}
cd ${tree_tagger_dir}
tar xvzf tree-tagger-linux-3.2.2.tar.gz

wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
tar xvzf tagger-scripts.tar.gz

wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh

wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz
gunzip english.par.gz

rm *.tar.gz

cd ..

mv ${tree_tagger_dir} app/src/PLN

cd app/src/PLN/${tree_tagger_dir}

sh install-tagger.sh

cd ${base_dir}

# 2.
# Installing git dependencies
wget https://download.pytorch.org/whl/cu75/torch-0.2.0.post2-cp36-cp36m-manylinux1_x86_64.whl
pip install torch-0.2.0.post2-cp36-cp36m-manylinux1_x86_64.whl
rm torch-0.2.0.post2-cp36-cp36m-manylinux1_x86_64.whl
pip install torchvision==0.2.2.post3

pip install git+https://github.com/miotto/treetagger-python/
pip install dlib==19.17.0

mkdir ${base_dir}/app/tmp

mkdir ${base_dir}/app/src/noticia_atual
