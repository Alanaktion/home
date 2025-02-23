#!/usr/bin/env python3
import argparse
from glob import glob
import json
import os
import sqlite3
import sys

from yt_dlp.options import parseOpts


"""
Use with `--exec ytdl-db.py` to handle a specific file after completion.
"""


def main():
    parser = argparse.ArgumentParser(
        description='write yt-dlp metadata into a database',
        epilog='mostly useful as a --exec handler when using yt-dlp')
    parser.add_argument('file', nargs='*')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='Delete JSON files after import')
    args, rest = parser.parse_known_intermixed_args()
    sys.argv = [sys.argv[0]] + rest

    ytparser, config, urls = parseOpts()
    infodir = config.paths.get('infojson')

    db = init_db(infodir)

    files: list[str] = []
    for f in args.file:
        files.append(os.path.splitext(os.path.basename(f))[0])

    os.chdir(infodir)
    for f in glob('**/*.info.json', recursive=True):
        base = os.path.basename(f)[:-10]
        if files and base not in files:
            continue
        info_import(f, db)
        if args.delete:
            os.unlink(f)

    db.close()


def init_db(infodir: str):
    dbpath = infodir.rstrip('/\\') + '.sqlite'
    db = sqlite3.connect(dbpath)

    def _table(table: str, cols: list[str]):
        db.execute("CREATE TABLE IF NOT EXISTS %s(%s)"
                   % (table, ','.join(cols)))

    _table('video', [
        'id', 'extractor', 'title', 'description', 'channel_id', 'uploader_id',
        'webpage_url', 'playlist_id', 'availability', 'age_limit',
        'live_status', 'uploader',
    ])
    _table('playlist', [
        'id', 'extractor', 'title', 'description', 'channel_id', 'uploader_id',
        'webpage_url', 'availability', 'uploader',
    ])

    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS video_id "
               "ON video(extractor, id)")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS playlist_id "
               "ON playlist(extractor, id)")
    db.commit()

    return db


def insert(db: sqlite3.Connection, table: str, data: dict):
    cols = ', '.join(data.keys())
    vals = ':' + ', :'.join(data.keys())
    db.execute("INSERT OR IGNORE INTO %s(%s) VALUES(%s)"
               % (table, cols, vals), data)
    db.commit()


def info_import(json_file: str, db: sqlite3.Connection):
    print(json_file)
    with open(json_file, 'rb') as fp:
        data = json.load(fp)
    vals = filter_dict(data, [
        'id', 'extractor', 'title', 'description', 'channel_id', 'uploader_id',
        'webpage_url', 'playlist_id', 'availability', 'age_limit',
        'live_status', 'uploader',
    ])
    insert(db, data['_type'], vals)


def filter_dict(val: dict, keep: list | tuple):
    return {k: v for k, v in val.items() if k in keep}


if __name__ == "__main__":
    main()
