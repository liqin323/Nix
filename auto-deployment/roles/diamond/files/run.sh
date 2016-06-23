#!/usr/bin/env bash

pip2.7 install diamond
pkill diamond
cat ./spvd.conf >> ../supervisor/supervisord.conf
supervisorctl reload