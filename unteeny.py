#!/usr/bin/env python3
import argparse
import glob
import os
import re
import sys

parser = argparse.ArgumentParser(
    description='delete extra images when multiple sizes/formats exist')
group = parser.add_mutually_exclusive_group()
group.add_argument('-f', '--format', choices=['jpg', 'webp'], default='jpg',
                   help='delete image specified format if PNG also exists')
group.add_argument('-w', '--wordpress', action='store_true',
                   help='delete WordPress thumbnails, keeping full-size')
parser.add_argument('-r', '--recursive', action='store_true')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp',)

re_thumb = re.compile(r'^(.+)-[0-9]+x[0-9]+$')
pattern = ('**/' if args.recursive else '') + (
    '*' if args.wordpress else ('*.' + args.format))
for f in glob.iglob(pattern, recursive=args.recursive):
    base, ext = os.path.splitext(f)

    # Handle "duplicates" in different formats
    if not args.wordpress:
        if os.path.exists(base + '.png'):
            if args.verbose:
                print('PNG exists, delete', args.format, f, file=sys.stderr)
            print(f)
            os.unlink(f)
        else:
            if args.verbose:
                print('PNG does not exist:', f, file=sys.stderr)
        continue

    # Handle WordPress thumbnails
    if ext.lower() not in SUFFIXES:
        if args.verbose:
            print('Not an image:', f, file=sys.stderr)
        continue
    _match = re.match(re_thumb, base)
    if not _match:
        if args.verbose:
            print('Not a thumbnail:', f, file=sys.stderr)
        continue
    if os.path.exists(_match.group(1) + ext):
        if args.verbose:
            print('Original exists, delete thumbnail:', f, file=sys.stderr)
        os.unlink(f)
    else:
        print('Not deleting thumbnail without original:', f, file=sys.stderr)
