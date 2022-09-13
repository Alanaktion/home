#!/bin/bash
# Deduplicates files >1M on a btrfs partition, in the working directory

fdupes -r -G 1000000 . | duperemove -d --fdupes
