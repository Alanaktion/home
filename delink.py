#!/usr/bin/env python3
import argparse
import os
import shutil

from pathlib import Path

parser = argparse.ArgumentParser(
    description='replace symlinks with copies of their targets')
parser.add_argument('-L', '--hard-link', action='store_true',
                    help='hard-link source file if possible')
parser.add_argument('path', default=os.getcwd(), nargs='*',
                    help='path to symlink, or directory containing symlinks')
args = parser.parse_args()


def _handle_link(path: Path):
    target = path.resolve()
    path2 = path.with_suffix(path.suffix + '~')
    path.rename(path2)
    if args.hard_link:
        try:
            path.hardlink_to(target)
        except OSError:
            shutil.copy(target, path)
    else:
        shutil.copy(target, path)
    path2.unlink(True)


for path in args.path:
    root = Path(path)
    if root.is_dir():
        for path in root.iterdir():
            if not path.is_symlink():
                continue
            _handle_link(path)
    elif root.is_symlink():
        _handle_link(root)
    else:
        parser.error('not a symlink or directory: ' + args.path)
