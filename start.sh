#!/bin/bash
clear 

rm -rf *.session* unknown*

PORT=${PORT:-8080}
gunicorn --bind 0.0.0.0:$PORT app:app &

python3 patch_sync.py
python3 -m main
