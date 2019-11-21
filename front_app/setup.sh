#!/usr/bin/env bash
virtualenv venv/ -p python3
source venv/bin/activate
pip install -r requirements.txt
mkdir front_app/tmp
