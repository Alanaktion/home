#!/bin/bash

# I recommend using my imgfind Python app instead, it includes a teeny command
# that handles many more cases for image optimization!
# https://github.com/Alanaktion/imgfind

set -e

#find . -name '*.png' -print \
#  -execdir sh -c "convert -format jpg -quality 85 '\$0' && rm '\$0'" {} \;

if [ $# -eq 0 ]; then
  #mogrify -format jpg -quality 85 *.png && rm *.png
  #mogrify -format jpg -quality 85 *.PNG && rm *.PNG
  #for f in $(magick identify -format "%[opaque]:%f\n" *.png *.PNG | grep "^True" | cut -d: -f2); do
  for f in *.png *.PNG *.tif *.tiff; do
    [ ! -f "$f" ] && continue
    suffix=$(tail -c 8 "$f" | grep -a IEND || true)
    if [ "$suffix" == '' ]; then
      echo Skip PNG with extra data: "$f"
    elif [ $(gm identify -ping -format "%A" "$f") == 'false' ]; then
      echo "$f"
      gm mogrify -format jpg -quality 85 "$f" && rm "$f"
    elif [ $(magick identify -format "%[opaque]" "$f") == 'True' ]; then
      echo "$f"
      gm mogrify -format jpg -quality 85 "$f" && rm "$f"
    else
      echo Crush: "$f"
      # pngcrush -ow "$f"
    fi
  done
else
  # TODO: only convert images without alpha channel, like we do in non-recursive operation above.
  # TODO: consider using gm batch
  find . -iname '*.png' -print \
    -execdir sh -c "gm mogrify -monitor -format jpg -quality 90 *.png && rm *.png" {} \;
fi
