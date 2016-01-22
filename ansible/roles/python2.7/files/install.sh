#!/usr/bin/env bash

tar -zxf Python-2.7.11.tgz

cd Python-2.7.11

./configure --prefix=/usr/local

sudo make && make altinstall

wget --no-check-certificate https://bootstrap.pypa.io/ez_setup.py -O - | python2.7 - --user

/root/.local/bin/easy_install-2.7 pip




