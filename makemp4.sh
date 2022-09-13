#!/bin/bash
function makemp4 () {
  for i in *.{mkv,avi,wmv,mpg,flv}; do
    [[ ! -f "$i" ]] && continue
    echo "$i"
    outfile="$i"
    outfile="${outfile/.mkv/.mp4}"
    outfile="${outfile/.avi/.mp4}"
    outfile="${outfile/.wmv/.mp4}"
    outfile="${outfile/.mpg/.mp4}"
    outfile="${outfile/.flv/.mp4}"
    if [[ ! -f "$outfile" ]]; then
      echo "$outfile"
      ffmpeg -i "$i" "$outfile"
    fi
  done
}
makemp4
