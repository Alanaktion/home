#!/bin/bash
set -e

# Flatten directories containing a single file from the current path
find . -maxdepth 1 -type d -not -path '.' | while read d; do
  count=$(ls -1q "$d" | wc -l)
  #echo $d $count
  if [[ $count -eq 1 ]]; then
    cd "$d"
    mv -n * ../
    cd ..
    rmdir "$d"
  fi
done
