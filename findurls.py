#!/usr/bin/env python3
import os
from argparse import ArgumentParser
from re import finditer
from sys import stderr

# TODO: accept stdin, single files, recursive, etc. args
parser = ArgumentParser(description='match and print URLs in the directory')
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("path", type=str, nargs='*', default=['.'])
args = parser.parse_args()


def search(file: str):
    with open(file, 'r') as f:
        for url in finditer(r"https?://[^\s\"'<]+", f.read()):
            if args.verbose:
                print(file, file=stderr)
            print(url.group(0))


for p in args.path:
    if os.path.isdir(p):
        for root, dirs, files in os.walk(p):
            for name in files:
                search(os.path.join(root, name))
    else:
        search(p)
