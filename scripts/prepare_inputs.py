#!/usr/bin/env python3
"""Prepare a 1 GiB donor filesystem and a verified local Lenovo hardware overlay.

Only ordinary image files are read. No device is flashed, mounted or modified.
Proprietary inputs remain local; this script never downloads or uploads them.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import struct
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = 4096


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def require_file(path):
    path = path.resolve()
    if not path.is_file() or str(path).startswith('/dev/'):
        raise ValueError('Expected a regular local input file, not a device: ' + str(path))
    return path


def image_header(path):
    with path.open('rb') as stream:
        stream.seek(1024)
        data = stream.read(1024)
    if len(data) != 1024 or data[56:58] != b'\x53\xef':
        raise ValueError('Expected a raw ext4 filesystem image: ' + str(path))
    block_size = 1024 << struct.unpack_from('<I', data, 24)[0]
    return block_size, struct.unpack_from('<I', data, 4)[0]


def transfer_ranges(text):
    numbers = [int(x) for x in text.split(',')]
    count = numbers.pop(0)
    if count != len(numbers) or count % 2:
        raise ValueError('Malformed transfer-list range')
    result = []
    for start, end in zip(numbers[0::2], numbers[1::2]):
        if not 0 <= start < end:
            raise ValueError('Invalid transfer-list range bounds')
        result.append((start, end))
    return result


def reconstruct(transfer, data_file, output):
    lines = transfer.read_text().strip().splitlines()
    version = int(lines[0])
    if version not in (1, 2, 3, 4):
        raise ValueError('Unsupported transfer-list version: ' + str(version))
    header = 2 if version == 1 else 4
    operations = []
    for line in lines[header:]:
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 2 or fields[0] not in ('new', 'zero', 'erase'):
            raise ValueError('Only full new/zero/erase images are supported; reject incremental OTA: ' + line)
        operations.append((fields[0], transfer_ranges(fields[1])))
    highest = max(end for _, pairs in operations for _, end in pairs)
    new_bytes = sum((end-start)*BLOCK for op, pairs in operations if op == 'new' for start, end in pairs)
    if data_file.stat().st_size != new_bytes:
        raise ValueError('system.new.dat size does not agree with transfer list')
    zeros = bytes(1024 * 1024)
    with output.open('w+b') as dst, data_file.open('rb') as src:
        dst.truncate(highest * BLOCK)
        for op, pairs in operations:
            for start, end in pairs:
                dst.seek(start * BLOCK)
                remaining = (end-start) * BLOCK
                while remaining:
                    n = min(remaining, len(zeros))
                    # erase is safe to zero in this offline full-image builder.
                    data = src.read(n) if op == 'new' else zeros[:n]
                    if len(data) != n:
                        raise ValueError('Short system.new.dat input')
                    dst.write(data)
                    remaining -= n
        if src.read(1):
            raise ValueError('Unconsumed system.new.dat bytes')


def run(argv, log, accepted=(0,)):
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    with log.open('a') as stream:
        stream.write('$ ' + ' '.join(str(x) for x in argv) + '\n' + result.stdout + '\n')
    if result.returncode not in accepted:
        raise RuntimeError('Command failed; see ' + str(log) + ': ' + str(argv[0]))


def quote(value):
    value = str(value)
    if any(c in value for c in ('\n', '\r', '"', '\\')):
        raise ValueError('Unsupported character in debugfs path')
    return '"' + value + '"'


def extract_image_file(image, name, destination, expected, log):
    relative = pathlib.PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe locked path: ' + name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # debugfs sometimes returns zero even when a command fails; verify the file and hash.
    if destination.exists():
        destination.unlink()
    run(['debugfs', '-R', 'dump -p ' + quote('/' + name) + ' ' + quote(destination), str(image)], log)
    if not destination.is_file() or digest(destination) != expected:
        raise ValueError('Hardware file mismatch or missing: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-boot', required=True, type=pathlib.Path)
    parser.add_argument('--stock-system', required=True, type=pathlib.Path)
    parser.add_argument('--donor-zip', required=True, type=pathlib.Path)
    parser.add_argument('--work', required=True, type=pathlib.Path)
    parser.add_argument('--lock', type=pathlib.Path, default=ROOT/'config/inputs.lock.json')
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text())
    boot, stock, donor = [require_file(p) for p in (args.stock_boot, args.stock_system, args.donor_zip)]
    work = args.work.resolve()
    if str(work).startswith('/dev/'):
        raise ValueError('Work directory must not be a device path')
    if work.exists() and any(work.iterdir()):
        raise ValueError('Choose a fresh empty work directory; existing inputs/outputs are never overwritten')
    for command in ('debugfs', 'e2fsck', 'resize2fs'):
        if not shutil.which(command):
            raise ValueError('Missing host dependency: ' + command)
    if digest(boot) != lock['stockBoot']['sha256']:
        raise ValueError('Unsupported stock boot/kernel baseline; do not bypass this identity check')
    if digest(donor) != lock['donor']['sha256']:
        raise ValueError('Donor ZIP SHA256 mismatch; obtain the pinned full image')
    if image_header(stock)[0] != BLOCK:
        raise ValueError('Stock filesystem must use 4096-byte blocks')
    work.mkdir(parents=True, exist_ok=True)
    outputs = [work/n for n in ('stock-boot.img', 'donor-boot.img', 'update-binary', 'donor-system.img', 'base-system.img')]
    if set(outputs) & {boot, stock, donor}:
        raise ValueError('Work output would overwrite an input')
    log = work/'prepare-inputs.log'
    log.write_text('Local input preparation; no device writes.\n')
    shutil.copyfile(boot, work/'stock-boot.img')
    selected = {
        'boot.img': 'donor-boot.img',
        'META-INF/com/google/android/update-binary': 'update-binary',
        'system.transfer.list': 'system.transfer.list',
        'system.new.dat': 'system.new.dat',
    }
    with zipfile.ZipFile(donor) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('Duplicate members in donor archive')
        for member, target in selected.items():
            with archive.open(member) as src, (work/target).open('wb') as dst:
                shutil.copyfileobj(src, dst)
    reconstruct(work/'system.transfer.list', work/'system.new.dat', work/'donor-system.img')
    if image_header(work/'donor-system.img')[0] != BLOCK:
        raise ValueError('Pinned donor did not reconstruct as a 4096-byte ext4 image')
    # Never resize the user's input: all writes here target a new work-local copy.
    shutil.copyfile(work/'donor-system.img', work/'base-system.img')
    run(['e2fsck', '-fy', str(work/'base-system.img')], log, (0, 1))
    run(['resize2fs', str(work/'base-system.img'), str(lock['systemPartitionBytes']//BLOCK)], log)
    with (work/'base-system.img').open('r+b') as stream:
        stream.truncate(lock['systemPartitionBytes'])
    # Old donor ext4 resize-inode accounting needs the same post-resize repair
    # as the original port workflow, followed by a separate read-only check.
    run(['e2fsck', '-fy', str(work/'base-system.img')], log, (0, 1))
    run(['e2fsck', '-fn', str(work/'base-system.img')], log)
    if image_header(work/'base-system.img') != (BLOCK, lock['systemPartitionBytes']//BLOCK):
        raise ValueError('Filesystem geometry does not fit the B8000-F system partition')
    overlay = work/'overlay/system'
    extracted = []
    for entry in lock['overlay']:
        target = pathlib.PurePosixPath(entry['target'])
        if target.is_absolute() or '..' in target.parts:
            raise ValueError('Unsafe overlay target')
        source = stock if entry['source'] == 'stock' else work/'donor-system.img'
        destination = overlay/pathlib.Path(*target.parts)
        extract_image_file(source, entry['path'], destination, entry['sha256'], log)
        extracted.append({'path':entry['target'], 'sha256':entry['sha256'], 'source':entry['source']})
    (work/'prepared-inputs.json').write_text(json.dumps({
        'status':'PASS', 'stockBootSha256':lock['stockBoot']['sha256'],
        'donorZipSha256':lock['donor']['sha256'], 'systemBytes':lock['systemPartitionBytes'],
        'overlay':extracted,
        'limitations':'Proprietary inputs stay local. Selected stock files are checked individually; no calibration/data partitions are consumed.'
    }, indent=2)+'\n')
    print(json.dumps({'status':'PASS','work':str(work),'overlayFiles':len(extracted),'baseSystemBytes':lock['systemPartitionBytes']}))


if __name__ == '__main__':
    main()
