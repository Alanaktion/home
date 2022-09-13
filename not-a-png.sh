#!/bin/bash
#find . -type f -name *.png -exec file -hi '{}' \; | grep -v image/png

# Rename files that are jpeg images with .png extensions

find . -type f -name "*.png" -print0 | while read -d $'\0' file; do
  isjpeg=$(file -hi "$file" | grep image/jpeg)
  if [[ "$isjpeg" ]]; then
    echo $file
    mv "$file" "${file/.png/.jpg}"
  fi
done
