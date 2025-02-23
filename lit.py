#!/usr/bin/env python3
import argparse
import array
import sys
import unicodedata


JA_ROM_MAP = {
    'chi': 'ti',
    'tsu': 'tu',
    'shi': 'si',
}

JA_ROM = [
    'ka', 'ke', 'ki', 'ko', 'ku',
    'ga', 'ge', 'gi', 'go', 'gu',
    'ma', 'me', 'mi', 'mo', 'mu',
    'na', 'ne', 'ni', 'no', 'nu',
    'ha', 'he', 'hi', 'ho', 'hu',
    'pa', 'pe', 'pi', 'po', 'pu',
    'ba', 'be', 'bi', 'bo', 'bu',
    'ta', 'te', 'ti', 'to', 'tu',
    'da', 'de', 'di', 'do', 'du',
    'sa', 'se', 'si', 'so', 'su',
    'za', 'ze', 'zi', 'zo', 'zu',
    'ra', 're', 'ri', 'ro', 'ru',
    'ya', 'yo', 'yu',
    'wa', 'wo', 'wu',
    'va', 've', 'vi', 'vo', 'vu',  # katakana-only
    # TODO: transliterate v* as vu+kana as it's more common
    # e.g. 'KATAKANA LETTER VU' + 'KATAKANA LETTER SMALL A'
    'a',  'e',  'i',  'o',  'u', 'n',
]

KO_CON_MAP = {
    'g': 'ㄱ',
    'n': 'ㄴ',
    'd': 'ㄷ',
    'l': 'ㄹ', 'r': 'ㄹ',
    'm': 'ㅁ',
    'b': 'ㅂ',
    'ng': 'ㅇ',
    's': 'ㅅ',
    'j': 'ㅈ',
    'ch': 'ㅊ', 'c': 'ㅊ',  # TODO: should this be translated elsewhere?
    'k': 'ㅋ',
    't': 'ㅌ',
    'p': 'ㅍ',
    'h': 'ㅎ',
}

KO_VOW_MAP = {
    'a': 'ㅏ',
    'ae': 'ㅐ',
    'eo': 'ㅓ',
    'e': 'ㅔ',
    'yeo': 'ㅕ',
    'ye': 'ㅖ',
    'o': 'ㅗ',
    'u': 'ㅜ',
    'eu': 'ㅡ',
    'i': 'ㅣ',
}

KAT = 'KATAKANA'
HIR = 'HIRAGANA'


def build_parser():
    parser = argparse.ArgumentParser(description='transliterate strings')

    lang = parser.add_argument_group('language', description='default=ja')
    l_group = lang.add_mutually_exclusive_group()
    l_group.add_argument('-j', '--ja', dest='lang', action='store_const',
                         const='ja', default='ja', help='Japanese 日本語')
    l_group.add_argument('-k', '--ko', dest='lang', action='store_const',
                         const='ko', help='Korean 한국어')

    system = parser.add_argument_group('writing system (ja romaji input)')
    s_group = system.add_mutually_exclusive_group()
    s_group.add_argument('-H', '--hiragana', dest='wsys', action='store_const',
                         const=HIR, default='hiragana')
    s_group.add_argument('-K', '--katakana', dest='wsys', action='store_const',
                         const=KAT)

    if sys.stdin.isatty():
        parser.add_argument('input', nargs='*',
                            help='text input to transliterate, or stdin')

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if sys.stdin.isatty():
        input = ' '.join(args.input).strip()
    else:
        input = sys.stdin.read().strip()

    if input.isascii():
        if args.lang == 'ja':
            out_str = input.translate(str.maketrans('l', 'r'))
            for k, v in JA_ROM_MAP.items():
                out_str = out_str.replace(k, v)
            for k in JA_ROM:
                if k not in out_str:
                    continue
                prefix = KAT if k[0] in ('v',) else args.wsys
                v = unicodedata.lookup(prefix + ' LETTER ' + k.upper())
                out_str = out_str.replace(k, v)
            # TODO: convert trailing 's' to 'su', etc?
        elif args.lang == 'ko':
            out_str = input
            for k, v in KO_CON_MAP.items():
                out_str = out_str.replace(k, v)
            for k, v in KO_VOW_MAP.items():
                out_str = out_str.replace(k, v)
            out_str = unicodedata.normalize('NFKC', out_str)
            # TODO: learn hangul lol

    else:
        out = array.array('B')
        rom_rev = {v: k for k, v in JA_ROM_MAP.items()}
        for c in input:
            data = unicodedata.name(c).split()
            char = data[-1].lower()
            if data[0] in (HIR, KAT) and char in rom_rev:
                char = rom_rev[char]
            if char == 'SPACE':
                out.frombytes(b' ')
            else:
                out.frombytes(char.encode('utf-8'))

        out_str = out.tobytes().decode('utf-8')

    sentences = out_str.split('. ')
    print('. '.join(s.capitalize() for s in sentences))


if __name__ == '__main__':
    main()
