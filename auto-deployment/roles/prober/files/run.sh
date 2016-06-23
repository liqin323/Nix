#!/usr/bin/env bash

pip2.7 install psutil
pip2.7 install PyYAML
cat ./spvd.conf >> ../supervisor/supervisord.conf
supervisorctl reload
