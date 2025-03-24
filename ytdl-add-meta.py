#!/usr/bin/env python3
import argparse
from glob import glob
import json
import os
import sys

from yt_dlp.options import parseOpts
from yt_dlp.postprocessor import FFmpegMetadataPP


def main():
    parser = argparse.ArgumentParser(
        description='embed metadata from infojson to a media file',
        epilog='this is basically --embed-metadata but after downloading.')
    parser.add_argument('file', nargs='*')

    args, rest = parser.parse_known_intermixed_args()
    sys.argv = [sys.argv[0]] + rest

    ytparser, config, urls = parseOpts()
    infodir = config.paths.get('infojson')

    files: list[str] = []
    for f in args.file:
        files.append(os.path.splitext(os.path.basename(f))[0])

    for f in glob('**/*.info.json', recursive=True, root_dir=infodir):
        base = os.path.basename(f)[:-10]
        if files and base not in files:
            continue
        media_file = None
        for mf in args.file:
            if os.path.splitext(os.path.basename(mf))[0] == base:
                media_file = mf
                break
        if media_file:
            add_metadata(media_file, os.path.join(infodir, f))


def add_metadata(media_file: str, json_file: str):
    print(media_file)
    with open(json_file, 'rb') as fp:
        data = json.load(fp)
    pp = FFmpegMetadataPP(None, True, False)
    data['filepath'] = media_file
    pp.run(data)


if __name__ == "__main__":
    main()
