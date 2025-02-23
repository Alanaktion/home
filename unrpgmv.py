#!/usr/bin/env python3
import argparse
import json
import os

from pathlib import Path


parser = argparse.ArgumentParser(description='decrypt RPG Maker MV game files')
parser.add_argument('gamedir', nargs='?', default=os.getcwd(),
                    help='game directory to decrypt')
parser.add_argument('--no-audio', dest='audio', action='store_false')
parser.add_argument('--no-images', dest='images', action='store_false')
parser.add_argument('-u', '--update', action='store_true',
                    help='update game asset loading to use decrypted files')
parser.add_argument('-D', '--delete', action='store_true',
                    help='delete original files after decrypting')
args = parser.parse_args()

# Determine game www directory
path = Path(args.gamedir)
if not path.match('www'):
    path /= 'www'


# Load encryption config
# TODO: Read ref header data from rpg_core.js in case it is different
SIGNATURE = "5250474d56000000"
VER = "000301"
REMAIN = "0000000000"

with (path / 'data/System.json').open('r') as f:
    system: dict = json.load(f)

hasEncryptedImages = system.get('hasEncryptedImages', True)
hasEncryptedAudio = system.get('hasEncryptedAudio', True)
headerlength = 16
encryptionKey = bytearray.fromhex(system.get('encryptionKey', ''))
refBytes = bytearray.fromhex(SIGNATURE + VER + REMAIN)


def decrypt(infile: Path, outfile: Path):
    with infile.open('rb') as f:
        check = f.read(headerlength)
        if check != refBytes:
            raise ValueError('Invalid header')

        header = bytearray(f.read(headerlength))
        for i, b in enumerate(header):
            header[i] = b ^ encryptionKey[i]

        if outfile.suffix == '.png' and b'PNG' not in header:
            raise ValueError('Invalid PNG')
        if outfile.suffix == '.ogg' and b'Ogg' not in header:
            raise ValueError('Invalid Ogg')

        with outfile.open('xb') as o:
            o.write(header)
            o.write(f.read())

    if args.delete:
        infile.unlink()


# Find decryptable files
for file in path.glob('**/*.rpgmv*'):
    if file.suffix == '.rpgmvp':
        if not args.images:
            continue
        outfile = file.with_suffix('.png')
    elif file.suffix == '.rpgmvo':
        if not args.audio:
            continue
        outfile = file.with_suffix('.ogg')
    else:
        print('Unknown encrypted file, using generic ext:')
        outfile = file.with_suffix('.dat')

    if outfile.exists():
        continue

    print(file.relative_to(path))
    decrypt(file, outfile)


if args.update:
    if args.images:
        system['hasEncryptedImages'] = False
    if args.audio:
        system['hasEncryptedAudio'] = False
    print('Updating System.json')
    with (path / 'data/System.json').open('w') as f:
        json.dump(system, f, ensure_ascii=False)
