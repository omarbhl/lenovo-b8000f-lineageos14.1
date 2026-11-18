#!/usr/bin/env python3
"""Reconstruct the reviewed B8000-F Binder patch from an exact stock boot input.

This is an exact-image binary adaptation, not a kernel source build. No input
image, output payload, or device-specific backup belongs in Git.
"""
import argparse
import gzip
import hashlib
import json
import pathlib
import struct
import subprocess
import zlib

STOCK_SHA256 = 'affdfb176e997ef7c21dcc38aa657965c37ffccfdfd78253fe87a6dd82adf731'
PATCHED_SHA256 = '2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768'
GZIP_START, GZIP_END = 18984, 4224640
PATCH_OFFSET = 0x31da94


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stock_kernel(boot):
    if boot[:8] != b'ANDROID!' or len(boot) < 2048:
        raise ValueError('Expected a legacy Android stock boot.img')
    size, page = struct.unpack_from('<I', boot, 8)[0], struct.unpack_from('<I', boot, 36)[0]
    if page != 2048 or size != 4224696 or page + size > len(boot):
        raise ValueError('Unsupported B8000-F stock kernel layout')
    kernel = boot[page:page+size]
    if sha(kernel) != STOCK_SHA256:
        raise ValueError('Stock kernel SHA256 does not match this exact-image patch; refusing other firmware revisions')
    return kernel


def patch_kernel(boot):
    original = stock_kernel(boot)
    old_gzip = original[GZIP_START:GZIP_END]
    image = gzip.decompress(old_gzip)  # Validates gzip CRC and ISIZE.
    if len(image) != 8877092 or struct.unpack_from('<I', old_gzip, len(old_gzip)-4)[0] != len(image):
        raise ValueError('Unexpected decompressed kernel size')
    if struct.unpack_from('<III', image, PATCH_OFFSET-8) != (0xe5954004, 0xe5959000, 0xe5943000):
        raise ValueError('Binder instruction context does not match the reviewed image')
    patched = bytearray(image)
    struct.pack_into('<I', patched, PATCH_OFFSET, 0xeaffffeb)
    try:
        compressed = subprocess.run(['gzip', '-n', '-9', '-c'], input=bytes(patched),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    except FileNotFoundError as exc:
        raise RuntimeError('GNU gzip is required (Ubuntu: sudo apt install gzip)') from exc
    if compressed[:4] != b'\x1f\x8b\x08\x00':
        raise ValueError('Expected GNU gzip -n with no optional header flags')
    if len(old_gzip) - len(compressed) != 7:
        raise ValueError('GNU gzip output differs from the reviewed compressor result: expected a 7-byte gap. '
                         'Use the documented Ubuntu20.04 GNU gzip environment; do not pad or truncate the stream.')
    # The stock decompressor supports FNAME. Seven bytes keep input_data_end and
    # its ISIZE word at the original positions; arbitrary trailing padding does not.
    header = bytearray(compressed[:10]); header[3] |= 8
    padded = bytes(header) + b'B8000!\0' + compressed[10:]
    if gzip.decompress(padded) != patched or len(padded) != len(old_gzip):
        raise ValueError('Patched gzip roundtrip or exact-size verification failed')
    crc, size = struct.unpack_from('<II', padded, len(padded)-8)
    if crc != zlib.crc32(patched) & 0xffffffff or size != len(patched):
        raise ValueError('Patched gzip CRC/ISIZE mismatch')
    result = original[:GZIP_START] + padded + original[GZIP_END:]
    if sha(result) != PATCHED_SHA256:
        raise ValueError('Patched kernel hash differs from reviewed payload; refusing to emit an unverified kernel')
    if any(image[i] != patched[i] for i in range(len(image)) if not PATCH_OFFSET <= i < PATCH_OFFSET+4):
        raise ValueError('Unexpected decompressed kernel differences')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-boot', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True, help='Patched kernel payload including MTK header')
    args = p.parse_args()
    if args.output.resolve() == args.stock_boot.resolve():
        p.error('Output must not overwrite the stock input')
    result = patch_kernel(args.stock_boot.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(json.dumps({'output': str(args.output), 'bytes': len(result), 'sha256': sha(result),
                      'originalKernelSha256': STOCK_SHA256, 'changedInstructionOffset': hex(PATCH_OFFSET),
                      'verification': 'exact stock hash; one reviewed ARM word; gzip CRC/ISIZE and exact patched hash'}, indent=2))


if __name__ == '__main__':
    main()
