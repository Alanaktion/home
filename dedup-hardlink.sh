#!/bin/bash
# Deduplicates files >250K on any partition, in the working directory

jdupes -r1L -X size+=:250k .
