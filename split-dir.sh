#!/bin/bash
dir_size=250
if [[ $1 ]]; then
    dir_size=$1
fi
prefix="folder"
if [[ $2 ]]; then
    prefix=$2
fi
n=$((`find . -maxdepth 1 -type f | wc -l`/$dir_size+1))

read -p "Split directory into sets of $dir_size files? [Enter]"

for i in `seq 1 $n`; do
    mkdir -p "$prefix$i";
    find . -maxdepth 1 -type f | sort | head -n $dir_size | while read f; do
        mv "$f" "$prefix$i/"
    done
done
