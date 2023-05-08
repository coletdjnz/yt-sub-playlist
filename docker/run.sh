#!/bin/sh

echo "$UPDATER_OPTS --cookies /cookies.txt"
python3 /src/update.py $UPDATER_OPTS --cookies /cookies.txt