#!/usr/bin/env python3
# This sorta extracts a .mht as if it was originally a wget -r instead

import argparse
import binascii
import email
import os
import re


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description='Unpack a .mht Web Archive file')
    parser.add_argument('-f', '--force', action='store_true',
                        help='overwrite existing output files')
    parser.add_argument('file', type=argparse.FileType('r'))
    parser.add_argument('outdir', nargs='?', default=os.getcwd())
    return parser


def address_to_path(address: str, subtype: str = 'html') -> str:
    """Convert a source web-page address to a relative file path"""
    _address = re.sub(r'^https?://', '', address)
    if _address.endswith('/'):
        _address += f'index.{subtype}'
    return _address


def main():
    args = build_arg_parser().parse_args()

    root, ext = os.path.splitext(args.file.name)
    name = os.path.basename(root)
    if ext.lower() != '.mht':
        print('WARN: not a .mht file suffix')

    msg = email.message_from_file(args.file)
    args.file.close()
    for d in msg.defects:
        print('WARN:', d)

    # Create directory for output files
    os.chdir(args.outdir)
    with open(name + '.metadata.txt', 'w' if args.force else 'x') as f:
        f.writelines(': '.join(t) + '\n' for t in msg.items())

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart' or part.is_multipart():
            continue

        # Determine output path for part
        subtype = part.get_content_subtype()
        path = address_to_path(part['Content-Location'], subtype)
        print(path)

        # Write content to path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if part['content-transfer-encoding'] == 'base64':
            payload = part.get_payload()
            if not isinstance(payload, str):
                continue
            result = binascii.a2b_base64(payload)
        else:
            payload = part.get_payload(decode=True)
            if isinstance(payload, str):
                result = payload.encode()
            elif not isinstance(payload, bytes):
                continue
            else:
                result = payload
        with open(path, 'wb' if args.force else 'xb') as f:
            f.write(result)


if __name__ == '__main__':
    main()
