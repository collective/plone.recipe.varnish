#!/bin/sh
rm -r ./lib ./include ./local ./bin
virtualenv -p python2.7 .
./bin/pip install --upgrade -r requirements.txt
./bin/buildout
