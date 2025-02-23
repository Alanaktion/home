#!/usr/bin/env python3
import fnmatch
import os
import shutil
import subprocess

from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(
        description="Reduplicate files by replacing links with copies",
    )
    parser.add_argument(
        '-g', '--glob', type=str,
        help='Match files with this glob pattern',
    )
    parser.add_argument(
        "--no-recurse", dest="recursive", action="store_false",
        help="Do not recursively scan subdirectories",
    )
    parser.add_argument(
        "-l", "--dry-run", action="store_true",
        help="List target files without deduplicating",
    )
    parser.add_argument(
        "dir", nargs='*', default=['.'],
    )

    class Args:
        glob: str
        recursive: bool
        dry_run: bool
        log_level: int
        dir: list[str]

    return parser.parse_args(namespace=Args)


def main():
    args = parse_args()
    result = subprocess.run(['fdupes', '-H', '-q', '-r'] + args.dir,
                            capture_output=True)
    for group in result.stdout.strip().split(bytes("\n\n", 'utf-8')):
        files = group.split(bytes("\n", 'utf-8'))
        first = str(files[0], 'utf-8')
        if args.glob and not fnmatch.fnmatch(first, args.glob):
            continue
        print(len(files), first)
        for file in files[1:]:
            if os.path.samefile(files[0], file):
                if args.dry_run:
                    print(file)
                else:
                    os.unlink(file)
                    shutil.copy(files[0], file)


if __name__ == '__main__':
    main()
