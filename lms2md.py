#!/usr/bin/env python3
import argparse
import json
import os
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        description='convert LM Studio conversation json to Markdown')

    parser.add_argument('-u', '--user', choices=('quote', 'headings'),
                        default='quote', help='output of user messages')
    parser.add_argument('-t', '--think', choices=('details', 'quote', 'none'),
                        default='details', help='output of reasoning/thinking')

    parser.add_argument('input', nargs='*', help='input files',
                        type=argparse.FileType('r', encoding='UTF-8'))

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    for f in args.input:
        data = json.load(f)
        if f.name == '<stdin>':
            out = sys.stdout
        else:
            outname = os.path.splitext(f.name)[0] + '.md'
            out = open(outname, 'w')

        out.write(f'# {data['name']}\n\n')

        for m in data['messages']:
            for v in m['versions']:
                if args.user == 'headings':
                    out.write(f'## {v['role']}')
                for c in v.get('content', []):
                    if c.get('isStructural'):
                        continue
                    if c['type'] == 'text':
                        prefix = '> ' if args.user == 'quote' and v['role'] == 'user' else ''
                        for line in c['text'].splitlines():
                            out.write(prefix + line + '\n')
                for s in v.get('steps', []):
                    prefix = ''
                    thinking = s.get('style', {}).get('type') == 'thinking'
                    if thinking:
                        if args.think == 'none':
                            continue
                        elif args.think == 'quote':
                            prefix = '> '
                        elif args.think == 'details':
                            out.write(f'<details>\n<summary>{s['style'].get('title', 'Thinking')}</summary>')
                    for c in s.get('content', []):
                        if c.get('isStructural'):
                            continue
                        if c['type'] == 'text':
                            for line in c['text'].splitlines():
                                out.write(prefix + line + '\n')
                    if thinking and args.think == 'details':
                        out.write('</details>\n')

            out.write('\n')

        f.close()
        out.close()


if __name__ == '__main__':
    main()
