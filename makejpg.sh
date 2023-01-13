#!/bin/bash

set -e

#find . -name '*.png' -print \
#  -execdir sh -c "convert -format jpg -quality 85 '\$0' && rm '\$0'" {} \;

if [ $# -eq 0 ]; then
  #mogrify -format jpg -quality 85 *.png && rm *.png
  #mogrify -format jpg -quality 85 *.PNG && rm *.PNG
  #for f in $(magick identify -format "%[opaque]:%f\n" *.png *.PNG | grep "^True" | cut -d: -f2); do
  for f in *.png *.PNG; do
    #magick identify -format "%[opaque]:%f\n" "$f"
    if [ $(magick identify -format "%[opaque]" "$f") == 'True' ]; then
      echo "$f"
      mogrify -format jpg -quality 85 "$f" && rm "$f"
    else
      echo Skip: "$f"
    fi
  done
else
  # TODO: only convert images without alpha channel, like we do in non-recursive operation above.
  find . -name '*.png' -print \
    -execdir sh -c "mogrify -format jpg -quality 85 *.png && rm *.png" {} \;
fi
