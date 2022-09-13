#!/bin/bash
dir_size=500
dir_name="folder"
n=$((`find . -maxdepth 1 -type f | wc -l`/$dir_size+1))

read -p "Split directory into sets of 500 files? [Enter]"

for i in `seq 1 $n`; do
    mkdir -p "$dir_name$i";
    find . -maxdepth 1 -type f | head -n $dir_size | while read f; do
        mv "$f" "$dir_name$i/"
    done
done

