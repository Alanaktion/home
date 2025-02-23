#!/usr/bin/env python3
import argparse
import os

from pathlib import Path

parser = argparse.ArgumentParser(
    description='modify symlink targets via string substitution')
parser.add_argument('-r', '--recursive', action='store_true')
parser.add_argument('-d', '--dry-run', action='store_true')
parser.add_argument('search')
parser.add_argument('replace')
args = parser.parse_args()

root = os.getcwd()
pattern = '**/*' if args.recursive else '*'
for path in Path(root).glob(pattern):
    if not path.is_symlink():
        continue

    target = os.readlink(path.as_posix())
    if args.search in target:
        newtarget = target.replace(args.search, args.replace)
        print(target, newtarget)
        if not args.dry_run:
            path.unlink()
            path.symlink_to(newtarget)
