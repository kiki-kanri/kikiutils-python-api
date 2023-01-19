#!/bin/sh

python3.11 setup.py sdist bdist_wheel
python3.11 -m twine upload dist/*
rm -rf build
rm -rf dist
rm -rf kiki_utils_api.egg-info
