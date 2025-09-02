#!/bin/sh
# Usage: ./fetchsplit.sh URL
# set -x
URL="$1"
CHUNKSIZE=$((2 * 1024 * 1024 * 1024)) # 2 GiB

if [ -z "$URL" ]; then
  echo "Usage: $0 URL"
  exit 1
fi

# Get filename from URL if possible
FILENAME=$(basename "${URL%%\?*}")
[ -z "$FILENAME" ] && FILENAME="download"

URL=$(curl -sIL -w '%{url_effective}' -o /dev/null "$URL")

# Get file size (Content-Length)
FILESIZE=$(curl -sIL "$URL" | awk 'BEGIN{IGNORECASE=1} /^Content-Length/ {size=$2} END{print size}' | tr -d '\r')

if [ -z "$FILESIZE" ]; then
  echo "Could not determine file size. Server may not send Content-Length."
  exit 1
fi

echo "Downloading $FILENAME ($FILESIZE bytes)"

i=0
START=0

while [ "$START" -lt "$FILESIZE" ]; do
  END=$((START + CHUNKSIZE - 1))
  if [ "$END" -ge "$FILESIZE" ]; then
    END=$((FILESIZE - 1))
  fi

  OUTFILE="${FILENAME}.part$(printf "%03d" $i)"
  echo "Fetching bytes $START-$END -> $OUTFILE"

  curl -r "$START"-"$END" -o "$OUTFILE" "$URL"
  if [ $? -ne 0 ]; then
    echo "Download failed for chunk $i"
    exit 1
  fi

  START=$((END + 1))
  i=$((i + 1))
done

echo "Done. Parts saved as ${FILENAME}.partNNN"
