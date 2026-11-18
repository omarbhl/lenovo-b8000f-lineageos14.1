#!/usr/bin/env python3
"""Pack a public-default B8000-F boot image from explicit contributor inputs."""
import argparse
import gzip
import hashlib
import json
import pathlib
import re
import struct

PARTITION_SIZE = 6291456


def sha(data):
    return hashlib.sha256(data).hexdigest()


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def read_boot(data):
    if data[:8] != b'ANDROID!' or len(data) < 2048:
        raise ValueError('Expected a legacy Android boot image')
    page = u32(data, 36)
    if page != 2048:
        raise ValueError('Only the inspected 2048-byte boot page layout is supported')
    offset = page + ((u32(data, 8)+page-1)//page)*page
    ramdisk = data[offset:offset+u32(data, 16)]
    if len(ramdisk) != u32(data, 16):
        raise ValueError('Truncated boot ramdisk')
    return page, ramdisk


def read_cpio(data):
    entries = {}; pos = 0
    while pos+110 <= len(data):
        magic = data[pos:pos+6]
        if magic not in (b'070701', b'070702'):
            raise ValueError('Invalid newc archive header')
        fields = [int(data[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
        if fields[11] < 1 or pos+110+fields[11] > len(data):
            raise ValueError('Invalid newc archive member name')
        name = data[pos+110:pos+110+fields[11]-1].decode()
        if name == 'TRAILER!!!':
            return entries
        if name in entries or name.startswith('/') or '..' in pathlib.PurePosixPath(name).parts:
            raise ValueError('Duplicate or unsafe archive member: '+name)
        start = (pos+110+fields[11]+3)&~3
        payload = data[start:start+fields[6]]
        if len(payload) != fields[6]:
            raise ValueError('Truncated newc archive member')
        if magic == b'070702' and sum(payload) & 0xffffffff != fields[12]:
            raise ValueError('Invalid newc CRC')
        entries[name] = {'fields': fields, 'data': payload}
        pos = (start+fields[6]+3)&~3
    raise ValueError('No newc trailer found')


def record(name, fields, data):
    fields = list(fields); fields[6] = len(data); fields[11] = len(name.encode())+1; fields[12] = 0
    header = b'070701'+b''.join(('%08x'%v).encode() for v in fields)
    result = header+name.encode()+b'\0'; result += b'\0'*((-len(result))%4)
    return result+data+b'\0'*((-len(data))%4)


def pack_boot(stock, donor, init, device_root, kernel=None):
    stock_page, _ = read_boot(stock)
    _, donor_ramdisk = read_boot(donor)
    if donor_ramdisk[:4] == struct.pack('<I',0x58881688):
        if u32(donor_ramdisk,4) != len(donor_ramdisk)-512:
            raise ValueError('Invalid donor MTK ramdisk length')
        donor_ramdisk = donor_ramdisk[512:]
    entries = read_cpio(gzip.decompress(donor_ramdisk))
    if init[:5] != b'\x7fELF\x01' or struct.unpack_from('<H',init,18)[0] != 40:
        raise ValueError('Init must be the compiled ARM32 ELF executable')
    if b'B8000 legacy bring-up: kernel SELinux is intentionally disabled' not in init:
        raise ValueError('Init does not contain the B8000 compatibility marker')

    def put(name, data, mode=None):
        if name in entries:
            fields = list(entries[name]['fields']); fields[5] = 0
        else:
            fields = [len(entries)+1,0o100644,0,0,1,0,len(data),0,0,0,0,len(name.encode())+1,0]
        if mode is not None:
            fields[1] = mode
        entries[name] = {'fields':fields, 'data':data}

    put('init',init,0o100750)
    for name in ['fstab.mt6589','init.mt8389.rc','init.mt6589.usb.rc','init.modem.rc','init.protect.rc','ueventd.mt8389.rc']:
        put(name,(device_root/name).read_bytes(),0o100644)
    put('fstab.mt8389',(device_root/'fstab.mt6589').read_bytes(),0o100644)
    usb = entries['init.mt6589.usb.rc']['data'].decode().replace('setprop sys.usb.vid 0408','setprop sys.usb.vid 17ef')
    usb, count = re.subn(r'(on property:sys\.usb\.config=mtp,adb\n.*?idProduct )[^\s]+',r'\g<1>76ff',usb,count=1,flags=re.S)
    if count != 1:
        raise ValueError('Cannot locate expected donor mtp,adb USB section')
    put('init.mt6589.usb.rc',usb.encode(),0o100644)
    initrc = entries['init.rc']['data'].decode().replace('import /init.${ro.hardware}.rc','import /init.mt8389.rc')
    if 'import /init.mt8389.rc' not in initrc:
        raise ValueError('Cannot locate hardware init import')
    # This uses the clean donor ramdisk. Never accept a reused diagnostic ramdisk.
    if 'b8000_capture' in initrc:
        raise ValueError('Donor contains a project diagnostic service; use the pinned original donor')
    initrc += '\non property:cm.service.adb.root=1\n    restart adbd\n\non property:cm.service.adb.root=0\n    restart adbd\n'
    put('init.rc',initrc.encode(),0o100750)
    if re.search(r'^\s*disabled\s*$',entries['init.zygote32.rc']['data'].decode(),re.M):
        raise ValueError('Donor zygote is disabled; use the pinned clean donor')
    put('init.usb.rc',entries['init.usb.rc']['data'].replace(b' --root_seclabel=u:r:su:s0',b''))
    put('ueventd.rc',entries['ueventd.rc']['data']+b'\n# Lenovo board rules\n'+(device_root/'ueventd.mt8389.rc').read_bytes())
    props = entries['default.prop']['data'].decode()
    overrides = {'ro.secure':'1','ro.adb.secure':'1','ro.b8000.legacy_kernel':'true',
                 'ro.b8000.build.status':'experimental-untested','persist.sys.root_access':'0','cm.service.adb.root':'0'}
    lines = [line for line in props.splitlines() if line.split('=',1)[0].strip() not in overrides]
    lines += [name+'='+value for name,value in overrides.items()]
    put('default.prop',('\n'.join(lines)+'\n').encode())
    entries.pop('adb_keys',None); entries.pop('b8000-capture.sh',None)
    rebuilt = b''.join(record(name,e['fields'],e['data']) for name,e in entries.items())+record('TRAILER!!!',[0]*13,b'')
    compressed = gzip.compress(rebuilt,compresslevel=9,mtime=0)
    # Python3.11 delegated mtime0 to zlib and exposed its OS byte; standardize it.
    compressed = compressed[:9]+b'\xff'+compressed[10:]
    ramdisk = struct.pack('<II32s472s',0x58881688,len(compressed),b'ROOTFS',b'\xff'*472)+compressed
    if kernel is None:
        kernel = stock[stock_page:stock_page+u32(stock,8)]
    if len(kernel) != 4224696 or kernel[:4] != struct.pack('<I',0x58881688):
        raise ValueError('Unexpected MTK kernel payload layout')
    if sha(kernel) not in ('affdfb176e997ef7c21dcc38aa657965c37ffccfdfd78253fe87a6dd82adf731',
                            '2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768'):
        raise ValueError('Unsupported kernel payload hash')
    if (u32(stock,12),u32(stock,20),u32(stock,32)) != (0x10008000,0x11000000,0x10000100):
        raise ValueError('Stock boot addresses do not match inspected B8000-F layout')
    header = bytearray(stock[:stock_page]); struct.pack_into('<I',header,8,len(kernel)); struct.pack_into('<I',header,16,len(ramdisk)); struct.pack_into('<I',header,24,0)
    cmd = b'androidboot.hardware=mt8389'; header[64:576] = cmd+b'\0'*(512-len(cmd))
    digest = hashlib.sha1(kernel+struct.pack('<I',len(kernel))+ramdisk+struct.pack('<I',len(ramdisk))+struct.pack('<I',0)).digest()
    header[576:608] = digest+b'\0'*12
    align = lambda b:b+b'\0'*((-len(b))%stock_page)
    result = bytes(header)+align(kernel)+align(ramdisk)
    used = len(result)
    if used > PARTITION_SIZE:
        raise ValueError('Boot image exceeds actual B8000-F boot partition')
    result += b'\0'*(PARTITION_SIZE-used)
    report = {'bootSha256':sha(result),'kernelSha256':sha(kernel),'initSha256':sha(init),
              'usedBytes':used,'partitionBytes':PARTITION_SIZE,'publicDefaults':True,
              'members':[{'name':n,'mode':oct(e['fields'][1]),'bytes':len(e['data']),'sha256':sha(e['data'])} for n,e in entries.items()]}
    return result, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-boot',type=pathlib.Path,required=True)
    p.add_argument('--donor-boot',type=pathlib.Path,required=True)
    p.add_argument('--init',type=pathlib.Path,required=True)
    p.add_argument('--device-root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]/'device/lenovo/b8000/rootdir')
    p.add_argument('--kernel',type=pathlib.Path,help='Reviewed patched MTK kernel payload; stock kernel used if omitted')
    p.add_argument('--output',type=pathlib.Path,required=True)
    args = p.parse_args()
    if args.output.resolve() in [v.resolve() for v in [args.stock_boot,args.donor_boot,args.init]+([args.kernel] if args.kernel else [])]:
        p.error('Output must not overwrite an input file')
    image, report = pack_boot(args.stock_boot.read_bytes(),args.donor_boot.read_bytes(),args.init.read_bytes(),args.device_root,args.kernel.read_bytes() if args.kernel else None)
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_bytes(image)
    args.output.with_suffix(args.output.suffix+'.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='members'},indent=2))


if __name__ == '__main__':
    main()
