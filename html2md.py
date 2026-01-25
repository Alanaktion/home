#!/usr/bin/python
import argparse
import html.parser
import re
import sys


def build_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('r'))
    # parser.add_argument('-e', '--root-element')
    parser.add_argument(
        '-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    return parser


class MarkdownHTMLParser(html.parser.HTMLParser):
    TAG_HEADINGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    TAG_PARAGRAPH = ('p', 'blockquote')
    TAG_HR = ('hr',)
    TAG_LINK = ('a',)
    TAG_IMAGE = ('img',)
    TAG_INLINE = ('span', 'b', 'i', 'strong', 'em',)

    def __init__(self):
        self.ALL_TAGS = self.TAG_HEADINGS + self.TAG_PARAGRAPH + self.TAG_HR \
            + self.TAG_LINK + self.TAG_IMAGE + self.TAG_INLINE
        self.markdown = ''
        self.tag_stack: list[str] = []
        self.attrs = {}
        super().__init__(convert_charrefs=True)

    def attr_dict(self, attrs: list[tuple]) -> dict[str, str]:
        return {t[0]: t[1] for t in attrs}

    def handle_starttag(self, tag, _attrs):
        self.tag_stack.append(tag)
        if tag in self.TAG_HEADINGS:
            self.markdown += '#' * int(tag[1:]) + ' '
            return
        if tag in self.TAG_INLINE:
            if tag in ('i', 'em'):
                self.markdown += '*'
            elif tag in ('b', 'strong'):
                self.markdown += '**'
            return
        if tag in ('blockquote',):
            self.markdown += '> '
        if tag in self.TAG_HR:
            self.markdown += '\n---\n'
        attrs = self.attr_dict(_attrs)
        self.attrs = attrs
        if tag in self.TAG_IMAGE:
            self.markdown += f"![{attrs.get('alt')}]({attrs.get('src')})"
            return
        if tag in self.TAG_LINK:
            self.markdown += '['

    def handle_endtag(self, tag):
        self.tag_stack.pop()
        if tag in self.TAG_INLINE:
            if tag in ('i', 'em'):
                self.markdown += '*'
            elif tag in ('b', 'strong'):
                self.markdown += '**'
            return
        if tag in self.TAG_PARAGRAPH or tag in self.TAG_HEADINGS:
            self.markdown += '\n'
            return
        if tag in self.TAG_LINK:
            self.markdown += f"]({self.attrs.get('href')})"

    def handle_data(self, data):
        if not len(self.tag_stack):
            return
        tag = self.tag_stack[-1]
        if tag not in self.ALL_TAGS:
            return
        self.markdown += data


def html_to_markdown(html):
    hp = MarkdownHTMLParser()
    hp.feed(html)

    return re.sub(r'[\n]{2,}', r'\n\n', hp.markdown).strip()


if __name__ == '__main__':
    args = build_arg_parser().parse_args()
    html = args.file.read()
    args.file.close()
    md = html_to_markdown(html)
    print(md, file=args.output)
