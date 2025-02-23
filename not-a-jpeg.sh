#!/bin/bash
#find . -type f -name *.jpg -exec file -hi '{}' \; | grep -v image/jpeg

# Rename files that are png images with .jpg extensions

find . -type f -name "*.jpg" -print0 | while read -d $'\0' file; do
  ispng=$(file -hi "$file" | grep image/png)
  if [[ "$ispng" ]]; then
    echo $file
    mv -n "$file" "${file/.jpg/.png}"
  fi
done
