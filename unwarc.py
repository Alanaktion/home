#!/usr/bin/env python3
import argparse
import gzip
import io
import itertools
import os
import zipfile
import zlib
from urllib.parse import unquote, urlsplit

# Most filesystems cap a single name at 255 bytes
MAX_NAME_BYTES = 255
CHUNK_SIZE = 128 * 1024
# Give up looking for the end of an HTTP header block after this much, so a
# record missing its blank separator line can't buffer without bound
MAX_HTTP_HEADER = 1 << 20


def clean_segment(segment):
    """Make a single URL path segment safe to use as a filename"""
    segment = segment.replace('\0', '').replace(os.sep, '_')
    if os.altsep:
        segment = segment.replace(os.altsep, '_')
    if segment in ('', '.', '..'):
        return '_' + segment
    # Truncate over-long names, keeping the extension intact
    encoded = segment.encode('utf-8', 'surrogatepass')
    if len(encoded) > MAX_NAME_BYTES:
        stem, ext = os.path.splitext(segment)
        ext = ext.encode('utf-8', 'surrogatepass')[:MAX_NAME_BYTES]
        stem = stem.encode('utf-8', 'surrogatepass')[:MAX_NAME_BYTES - len(ext)]
        segment = (stem + ext).decode('utf-8', 'ignore')
    return segment


def url_to_path(url, strip_query=False):
    """Map a URL to a local ./{hostname}/{file_path} relative path"""
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https'):
        return None

    host = parts.hostname
    if not host:
        return None
    if parts.port:
        host += '_' + str(parts.port)

    path = unquote(parts.path)
    segments = [clean_segment(s) for s in path.split('/') if s not in ('', '.')]

    # Directory-style URLs (and bare hosts) become index.html, like wget does
    if not segments or path.endswith('/'):
        segments.append('index.html')

    if parts.query and not strip_query:
        segments[-1] = clean_segment(segments[-1] + '?' + unquote(parts.query))

    return os.path.join(clean_segment(host), *segments)


def prepare_path(path):
    """Create parent directories, resolving file/directory collisions"""
    parent = os.path.dirname(path)
    if parent and os.path.isfile(parent):
        # An earlier record wrote /a/b, now we need /a/b/c: turn it into an index
        os.replace(parent, parent + '.tmp')
        os.makedirs(parent, exist_ok=True)
        os.replace(parent + '.tmp', os.path.join(parent, 'index.html'))
    elif parent:
        os.makedirs(parent, exist_ok=True)

    # The reverse collision: /a/b exists as a directory, now we need /a/b itself
    if os.path.isdir(path):
        path = os.path.join(path, 'index.html')
    return path


def read_headers(stream):
    """Read a CRLF-delimited header block into a lowercase-keyed dict"""
    headers = {}
    name = None
    while True:
        line = stream.readline()
        if not line:
            break
        line = line.rstrip(b'\r\n')
        if not line:
            break
        if line[:1] in (b' ', b'\t') and name:
            # Continuation of the previous header's value
            headers[name] += ' ' + line.strip().decode('utf-8', 'replace')
            continue
        name, _, value = line.partition(b':')
        name = name.strip().lower().decode('utf-8', 'replace')
        headers[name] = value.strip().decode('utf-8', 'replace')
    return headers


def iter_records(stream):
    """Yield (headers, block) per WARC record, block being a chunk generator

    Anything the caller leaves unread in a block is drained before the next
    record, so callers can skip records they don't care about.
    """
    while True:
        line = stream.readline()
        if not line:
            return
        if not line.strip():
            # Records are separated by two blank lines
            continue
        if not line.startswith(b'WARC/'):
            raise ValueError(f'Expected a WARC record, got {line[:40]!r}')

        headers = read_headers(stream)
        try:
            length = int(headers.get('content-length', 0))
        except ValueError:
            length = 0

        block = read_block(stream, length)
        yield headers, block
        for _ in block:
            pass


def read_block(stream, length):
    """Yield a record's content block in chunks"""
    while length > 0:
        chunk = stream.read(min(length, CHUNK_SIZE))
        if not chunk:
            return
        length -= len(chunk)
        yield chunk


def split_http(block):
    """Pull the HTTP header block off the front of a record

    Returns the parsed headers and whatever body bytes were read along with
    them, or (None, buffered) if no header terminator turns up.
    """
    buf = b''
    for chunk in block:
        buf += chunk
        end = buf.find(b'\r\n\r\n')
        if end >= 0:
            head = io.BytesIO(buf[:end])
            head.readline()  # Skip the status line
            return read_headers(head), buf[end + 4:]
        if len(buf) > MAX_HTTP_HEADER:
            break
    return None, buf


def dechunk(chunks):
    """Undo HTTP chunked transfer-encoding over a stream of byte chunks"""
    buf = b''
    size = None
    for chunk in chunks:
        buf += chunk
        while True:
            if size is None:
                end = buf.find(b'\r\n')
                if end < 0:
                    break
                # Each chunk body is followed by a CRLF, so the line before a
                # size is usually empty
                line = buf[:end].split(b';')[0].strip()
                buf = buf[end + 2:]
                if not line:
                    continue
                try:
                    size = int(line, 16)
                except ValueError:
                    return  # Malformed; nothing sensible left to read
                if size == 0:
                    return  # Final chunk, trailer ignored
            take = min(size, len(buf))
            if take:
                yield buf[:take]
                buf = buf[take:]
                size -= take
            if size:
                break  # Need more data to finish this chunk
            size = None


def decompress(chunks, encoding):
    """Undo an HTTP content-encoding over a stream of byte chunks"""
    if encoding == 'gzip':
        decomp = zlib.decompressobj(zlib.MAX_WBITS | 32)
    elif encoding == 'deflate':
        decomp = zlib.decompressobj()
    else:
        yield from chunks
        return

    first = True
    for chunk in chunks:
        try:
            data = decomp.decompress(chunk)
        except zlib.error:
            if not first:
                return  # Partly decompressed already, so the rest is garbage
            # Servers labelling raw deflate as 'deflate' is common enough to
            # retry without the zlib wrapper; failing that, take it as-is
            try:
                decomp = zlib.decompressobj(-zlib.MAX_WBITS)
                data = decomp.decompress(chunk)
            except zlib.error:
                yield from itertools.chain([chunk], chunks)
                return
        first = False
        if data:
            yield data

    data = decomp.flush()
    if data:
        yield data


def record_payload(headers, block):
    """Yield the decoded response body for a record"""
    if not headers.get('content-type', '').startswith('application/http'):
        # Not an HTTP response envelope, so the block is the payload
        return block

    http, leading = split_http(block)
    if http is None:
        return itertools.chain([leading], block)

    data = itertools.chain([leading], block)
    if http.get('transfer-encoding', '').lower() == 'chunked':
        data = dechunk(data)
    return decompress(data, http.get('content-encoding', '').lower())

parser = argparse.ArgumentParser(
    description='Extract a WARC/WACZ web archive file')
parser.add_argument('-o', '--output', help='Output directory')
parser.add_argument('-d', '--delete', action='store_true',
    help='Delete original file after extraction')
parser.add_argument('-q', '--strip-query', action='store_true',
    help='Omit query strings from output paths, so asdf.jpg?v=1 writes to '
         'asdf.jpg (URLs differing only by query overwrite each other)')
parser.add_argument('file', help='Path to .warc/.wacz file to convert')
args = parser.parse_args()

# Determine file paths
src = os.path.expanduser(args.file)
if not os.path.isfile(src):
    raise FileNotFoundError()

src = os.path.abspath(src)

base, ext = os.path.splitext(src)
if ext == '.gz':
    # Strip the inner extension too, so foo.warc.gz extracts into foo/
    base, ext = os.path.splitext(base)

outdir = os.path.abspath(os.path.expanduser(args.output or base))
os.makedirs(outdir, exist_ok=True)
os.chdir(outdir)

if ext == '.wacz':
    # Extract WARC from WACZ first
    with zipfile.ZipFile(src) as z:
        z.extractall()
    if args.delete:
        os.unlink(src)
    src = os.path.join(outdir, 'archive/data.warc.gz')

# Per-record gzip members read back as one continuous stream, so a compressed
# WARC needs no special handling beyond opening it through gzip
opener = gzip.open if src.endswith('.gz') else open

count = 0
skipped = 0
with opener(src, 'rb') as stream:
    for headers, block in iter_records(stream):
        if headers.get('warc-type') != 'response':
            continue

        url = headers.get('warc-target-uri', '').strip('<>')
        path = url_to_path(url, args.strip_query) if url else None
        if path is None:
            skipped += 1
            continue

        path = prepare_path(os.path.join(outdir, path))
        with open(path, 'wb') as f:
            for chunk in record_payload(headers, block):
                f.write(chunk)
        count += 1

print(f'Extracted {count} files to {outdir}')
if skipped:
    print(f'Skipped {skipped} non-HTTP records')
if args.delete:
    os.unlink(src)
