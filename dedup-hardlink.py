#!/usr/bin/env python3
import argparse
import fnmatch
import os
import subprocess

parser = argparse.ArgumentParser(
    description="Deduplicate files by hard-linking, using fdupes"
)
parser.add_argument(
    "-s", "--min-size",
    type=int, default=250000,
    help="Minimum size of files, in bytes (default: 250KB)",
)
parser.add_argument(
    '-n', '--name', type=str,
    help='Match files with this glob pattern'
)
parser.add_argument(
    "--dry-run",
    dest="dry_run", action="store_true",
    help="List target files without deduplicating",
)
parser.add_argument(
    "path", type=str,
    metavar="dir", nargs='*', default=['.'],
)

args = parser.parse_args()

result = subprocess.run(
    ['fdupes', '-G', str(args.min_size), '-q', '-r'] + args.path,
    capture_output=True)

for group in result.stdout.strip().split(bytes("\n\n", 'utf-8')):
    files = group.split(bytes("\n", 'utf-8'))
    first = str(files[0], 'utf-8')
    if args.name and not fnmatch.fnmatch(first, args.name):
        continue
    print(len(files), first)
    if not args.dry_run:
        for file in files[1:]:
            tmppath = file + b'~'
            os.link(files[0], tmppath)
            os.unlink(file)
            os.rename(tmppath, file)
