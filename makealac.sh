#!/bin/bash

for i in *.flac; do
  ffmpeg -i "$i" -y -v 0 -vcodec copy -acodec alac  "${i%.flac}".m4a
done
