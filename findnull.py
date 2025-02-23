#!/usr/bin/env python3
import os
from argparse import ArgumentParser
from shlex import quote


def checknull(file: str, allow_empty: bool = False) -> bool:
    if not allow_empty and os.path.getsize(file) == 0:
        return False

    with open(file, "rb") as f:
        while True:
            content = f.read(4096)
            if not b"\x00" * len(content) == content:
                return False
            if len(content) < 4096:
                break
    return True


if __name__ == "__main__":
    parser = ArgumentParser(
        description="find files containing only null bytes")
    parser.add_argument("-z", "--zero", action="store_true",
                        help="include zero-length/empty files")
    parser.add_argument('--print', action='store_true',
                        help='print matching files')
    parser.add_argument('--exec', type=str,
                        help='execute this command on each file')
    parser.add_argument('--delete', action='store_true',
                        help='delete matching files')
    parser.add_argument("path", type=str, nargs="*", default=["."])
    args = parser.parse_args()

    def handle_file(file):
        if checknull(file, args.zero):
            if args.print or (not args.exec and not args.delete):
                print(file)
            if args.exec is not None:
                os.system(args.exec.replace('{}', quote(str(file))))
            if args.delete:
                os.unlink(file)

    for p in args.path:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                for name in files:
                    handle_file(os.path.join(root, name))
        else:
            handle_file(p)
