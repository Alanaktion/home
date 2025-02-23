#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


class Options(argparse.Namespace):
    prefix: bool = True
    # singles: bool = False
    recursive: bool = False
    verbose: bool = False
    dry_run: bool = False
    interactive: bool = False


def build_parser():
    parser = argparse.ArgumentParser(description='flatten a directory')
    parser.add_argument('-P', '--no-prefix', dest='prefix',
                        action='store_false',
                        help='do not prepend directory name to moved files')
    # parser.add_argument('-s', '--singles', action='store_true',
    #                     help='only flatten directories with a single file')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='rename files recursively')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true',
                       help='list changes as they are made')
    group.add_argument('-d', '--dry-run', action='store_true',
                       help='list changes but do not actually rename/move')
    group.add_argument('-i', '--interactive', action='store_true',
                       help='prompt for each change before applying')

    return parser


def main():
    args = build_parser().parse_args(namespace=Options)
    dirs = []
    pattern = '**/' if args.recursive else '*/'
    for d in Path('.').glob(pattern):
        for f in d.glob('*'):
            if f.is_dir():
                continue
            src = str(f)
            dest = str(f).replace('/', '-')
            if src == dest:
                continue
            if args.dry_run or args.interactive or args.verbose:
                print('mv', src, dest)
                if args.dry_run:
                    continue
                if args.interactive:
                    act = input('Rename? [Y/n] ')
                    if act != '' and act.lower()[0] != 'y':
                        continue
            os.rename(src, dest)
        sd = str(d)
        if sd != '.' and sd not in dirs:
            dirs.append(str(d))

    for d in sorted(dirs, reverse=True):
        if args.dry_run or args.interactive or args.verbose:
            print('rmdir', str(d))
            if args.dry_run:
                continue
        if args.interactive:
            act = input('Remove directory? [Y/n] ')
            if act != '' and act.lower()[0] != 'y':
                continue
        try:
            os.rmdir(d)
        except OSError:
            pass


if __name__ == '__main__':
    main()
