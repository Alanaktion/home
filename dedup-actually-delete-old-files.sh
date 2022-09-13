#!/bin/bash
# Deletes older identical files >1M in the working directory (recursively)
set -e
read -p "This will recursively delete identical files WITHOUT CONFIRMATION. Continue? [N/y] " -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
  echo
  echo "bye files <3 (starting 3 seconds)"
  echo
  sleep 3
  fdupes -r -G 1000000 -o ctime -i --delete --hardlinks --noprompt .
fi
