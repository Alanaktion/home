#!/bin/bash
set -e

# Flatten a single level of directories, prepending the dir name to moved files
find . -maxdepth 1 -type d -not -empty -not -path '.' | sed 's|./||' | while read d; do
  cd "$d"
  for f in *; do
    mv -n "$f" "../$d-$f"
  done
  cd ..
  rmdir "$d" || true
done
