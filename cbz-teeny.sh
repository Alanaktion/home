#!/bin/bash
# Optimize a CBZ/CBR comic archive with teeny

set -euo pipefail

if (( $# < 1 )); then
    echo "Usage: $0 INPUT.{CBZ|CBR} [OUTPUT.CBZ]" >&2
    exit 1
fi

in="$1"
out="${2:-${in%.*}_webp.cbz}" # default output name

orig_dir=$(pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT # clean up on exit

ext=${in##*.}
case "$ext" in
    cbz) fmt=zip ;;
    cbr) fmt=rar ;;
    *)   echo "Unsupported extension: $ext (must be .cbz or .cbr)" >&2; exit 1 ;;
esac

# Unpack
case "$fmt" in
    zip) unzip -q "$in" -d "$tmp" ;;
    rar)
        if command -v unrar >/dev/null; then
            unrar x -y "$in" "$tmp/" > /dev/null
        elif command -v unar >/dev/null; then
            unar -o "$tmp/" "$in" > /dev/null
        else
            7z e -o"$tmp" "$in" > /dev/null
        fi ;;
esac

# Run teeny (optimized WebP)
teeny -q -f webp -r "$tmp"

# Re‑package into the original working directory
# Always pack into zip archive, not rar
cd "$tmp" || exit
zip -qr "${orig_dir}/${out}" ./*

# rm "$in"
echo "$out"
