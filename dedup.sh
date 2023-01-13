#!/bin/bash
# Deduplicates files >250K on a btrfs partition, in the working directory

fdupes -r -G 250000 . | duperemove -d --fdupes
