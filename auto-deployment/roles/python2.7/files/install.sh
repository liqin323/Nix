#!/usr/bin/env bash

tar -zxf Python-2.7.11.tgz

cd Python-2.7.11

./configure --prefix=/usr/local

make && make altinstall




