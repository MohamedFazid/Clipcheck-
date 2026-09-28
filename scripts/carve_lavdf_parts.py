"""Extract LAV-DF files from single parts of its split zip, without downloading all 25 GB (CRC-32 checked).

    python scripts/carve_lavdf_parts.py --parts external_datasets/LAV-DF_parts/LAV-DF.zip.006 [--metadata-only | --list | --names FILE]"""
import argparse
import struct
import sys
import zlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_ROOT / 'external_datasets' / 'LAV-DF'
LOCAL_SIG = b'PK\x03\x04'
PREFIX = b'LAV-DF/'


def iter_members(buf):
    """Yield (name, method, crc, csize, usize, data_start) for every local header in buf whose compressed data lies wholly inside buf."""
    pos = buf.find(LOCAL_SIG)
    while pos != -1:
        head = buf[pos + 4:pos + 30]
        if len(head) == 26:
            _ver, flag, method, _t, _d, crc, csize, usize, nlen, elen = struct.unpack('<HHHHHIIIHH', head)
            name = buf[pos + 30:pos + 30 + nlen]
            start = pos + 30 + nlen + elen
            plausible = (name.startswith(PREFIX) and flag & 0x8 == 0 and method in (0, 8) and csize != 0xFFFFFFFF
                         and start + csize <= len(buf))
            if plausible:
                yield name.decode(), method, crc, csize, usize, start
                pos = buf.find(LOCAL_SIG, start + csize)
                continue
        pos = buf.find(LOCAL_SIG, pos + 4)


def inflate(buf, method, start, csize, usize, crc):
    raw = buf[start:start + csize]
    data = zlib.decompressobj(-15).decompress(raw) if method == 8 else bytes(raw)
    if len(data) != usize or (zlib.crc32(data) & 0xFFFFFFFF) != crc:
        return None
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--parts', nargs='+', required=True, help='one or more LAV-DF.zip.NNN part files')
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--list', action='store_true', help='only report what each part holds')
    mode.add_argument('--metadata-only', action='store_true', help='extract LAV-DF/metadata*.json (and README) only')
    mode.add_argument('--names', type=Path, help='text file, one member name per line (e.g. LAV-DF/test/000123.mp4)')
    args = ap.parse_args()

    wanted = None
    if args.names:
        wanted = {ln.strip() for ln in open(args.names) if ln.strip()}
    found = {}
    for part in sorted(args.parts):
        buf = Path(part).read_bytes()
        counts, written, bad = {}, 0, 0
        for name, method, crc, csize, usize, start in iter_members(buf):
            kind = name.split('/')[1] if name.count('/') >= 2 else 'top-level'
            counts[kind] = counts.get(kind, 0) + 1
            if args.list:
                continue
            if args.metadata_only:
                if not (name.startswith('LAV-DF/metadata') or name == 'LAV-DF/README.md'):
                    continue
            elif name not in wanted or name in found:
                continue
            data = inflate(buf, method, start, csize, usize, crc)
            if data is None:
                bad += 1
                continue
            dest = args.out / name.split('/', 1)[1]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            found[name] = dest
            written += 1
        print(f'{Path(part).name}: complete members {sum(counts.values())} {dict(sorted(counts.items()))}'
              + ('' if args.list else f'; extracted {written}; failed CRC/size {bad}'))
    if wanted is not None:
        missing = wanted - set(found)
        print(f'requested {len(wanted)}, extracted {len(found)}, not in the parts given {len(missing)}')
        if missing:
            sys.exit(1)


if __name__ == '__main__':
    main()
