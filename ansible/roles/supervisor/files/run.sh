#!/usr/bin/env bash

pip install supervisor
pkill supervisord
supervisord -c ./supervisord.conf