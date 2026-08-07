#!/bin/bash
in="$1"
out="${2:-${in%.*}.gif}"
width="${3:-480}"

ffmpeg -i "$in" -vf "fps=15,scale=$width:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse=dither=heckbert" -loop 0 "$out"
