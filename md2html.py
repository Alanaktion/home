#!/usr/bin/env python3
import argparse
import os

parser = argparse.ArgumentParser(
    description='Convert a Markdown document to HTML with styling')
parser.add_argument('-f', '--force', action='store_true',
                    help='Overwrite any destination .html file')
parser.add_argument('-c', '--compact', action='store_true',
                    help='Use a compact prose paragraph style')
parser.add_argument('file', help='Path to .md file to convert')
args = parser.parse_args()

# Determine file paths
src = os.path.expanduser(args.file)
if not os.path.isfile(src):
    raise FileNotFoundError()

base, ext = os.path.splitext(src)
dest = base + '.html'
if not args.force and os.path.isfile(dest):
    raise FileExistsError('destination file already exists')

# Convert the text with any available module
try:
    from markdown import markdownFromFile
    markdownFromFile(input=src, output=dest)
except ImportError:
    try:
        from markdown_it import MarkdownIt
        md = MarkdownIt()
        with open(src, 'r') as f:
            text = f.read()
        with open(dest, 'w') as f:
            f.write(md.render(text))
    except ImportError:
        import shutil
        import subprocess
        markdown_bin = shutil.which('markdown')
        if not markdown_bin:
            raise NotImplementedError('no supported markdown back-end found')
        subprocess.run([markdown_bin, '-G', '-o', dest, src])

# Add style block to file
extras = ''
if args.compact:
    extras += 'p + p {text-indent: 1em; margin-top: -1em;}\n'
else:
    extras += 'p {page-break-inside: avoid;}\n'

style = '''
<style type="text/css">
body {font-family: "Noto Serif", "Liberation Serif", serif;}
blockquote {border-left: 2px solid #999; margin-left: 0; padding-left: 1em;}
%s
</style>
<style type="text/css" media="print">
html, body {margin: 0;}
p {page-break-inside: avoid;}
</style>
''' % extras

with open(dest, 'a') as f:
    f.write(style)
