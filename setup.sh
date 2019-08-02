#!/usr/bin/env bash

# 1) Clone
git clone https://github.com/joaobarbirato/linkpics
cd linkpics

# 2) virtualenv
virtualenv venv/ -p python3.6
source venv/bin/activate

# #) requirements
pip3.6 install -r requirements.txt
