#!/bin/bash

for dir in */; do
  if [[ -d "$dir/.git" ]]; then
    pushd "$dir"
    git pull --all
    popd
  fi
done
