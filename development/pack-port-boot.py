#!/usr/bin/env python3
"""Rebuild the boot image preserving stock kernel and original CPIO metadata."""
import argparse, gzip, hashlib, json, pathlib, struct

project = pathlib.Path('/mnt/e/Lenovo Tablet Project')
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', type=pathlib.Path)
parser.add_argument('--kernel-file', type=pathlib.Path)
parser.add_argument('--hold-zygote', action='store_true')
parser.add_argument('--public-build', action='store_true', help='No pretrusted host key; authenticated non-root ADB by default')
args = parser.parse_args()
out = args.output_dir or project / 'rom/release'
out.mkdir(parents=True, exist_ok=True)
inspection = pathlib.Path((project/'device-inspection/latest-full.txt').read_text().strip().replace('E:\\','/mnt/e/').replace('\\','/'))
donor = (project/'donor-research/lineage14-unpacked/boot.img').read_bytes()
stock = (inspection/'extracted/boot.img').read_bytes()
u32 = lambda b, p: struct.unpack_from('<I', b, p)[0]
page = u32(donor,36)
ram_start = page + ((u32(donor,8)+page-1)//page)*page
ram = donor[ram_start:ram_start+u32(donor,16)]
if ram[:4] == struct.pack('<I',0x58881688): ram=ram[512:]
cpio = gzip.decompress(ram)
entries={}; pos=0
while pos+110 <= len(cpio):
    if cpio[pos:pos+6] not in (b'070701',b'070702'): raise RuntimeError('Bad newc header')
    fields=[int(cpio[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
    name=cpio[pos+110:pos+110+fields[11]-1].decode()
    if name=='TRAILER!!!': break
    start=(pos+110+fields[11]+3)&~3
    entries[name]={'fields':fields,'data':cpio[start:start+fields[6]]}
    pos=(start+fields[6]+3)&~3

def put(name,data,mode=0o100644):
    if name in entries:
        fields=list(entries[name]['fields']); fields[6]=len(data); fields[5]=0
    else: fields=[len(entries)+1,mode,0,0,1,0,len(data),0,0,0,0,len(name.encode())+1,0]
    fields[1]=mode
    entries[name]={'fields':fields,'data':data}

put('init',(project/'rom/compiled/init').read_bytes(),0o100750)
device=project/'rom/device/lenovo/b8000/rootdir'
for name in ['fstab.mt6589','init.mt8389.rc','init.mt6589.usb.rc','init.modem.rc','init.protect.rc','ueventd.mt8389.rc']:
    put(name,(device/name).read_bytes())
put('fstab.mt8389',(device/'fstab.mt6589').read_bytes())
usb=entries['init.mt6589.usb.rc']['data'].decode()
usb=usb.replace('setprop sys.usb.vid 0408','setprop sys.usb.vid 17ef')
import re
usb=re.sub(r'(on property:sys\.usb\.config=mtp,adb\n.*?idProduct )[^\s]+',r'\g<1>76ff',usb,count=1,flags=re.S)
put('init.mt6589.usb.rc',usb.encode())
initrc=entries['init.rc']['data'].decode().replace('import /init.${ro.hardware}.rc','import /init.mt8389.rc')
initrc += '''
on property:cm.service.adb.root=1
    restart adbd

on property:cm.service.adb.root=0
    restart adbd

on post-fs-data
    start b8000_capture

service b8000_capture /system/bin/sh /b8000-capture.sh
    disabled
    oneshot
    user root
    group root log
'''
put('b8000-capture.sh',b'''#!/system/bin/sh
mkdir -p /data/local/tmp/b8000-boot
chmod 0755 /data/local/tmp/b8000-boot
for n in 0 1 2; do
    dmesg > /data/local/tmp/b8000-boot/dmesg-$n.txt
    logcat -b all -d -v threadtime > /data/local/tmp/b8000-boot/logcat-$n.txt
    chmod 0644 /data/local/tmp/b8000-boot/*-$n.txt
    sleep 5
done
''',0o100750)
if args.public_build:
    initrc=initrc[:initrc.index('\non post-fs-data\n    start b8000_capture')]
    entries.pop('b8000-capture.sh',None)
put('init.rc',initrc.encode(),0o100750)
if args.hold_zygote:
    zygote = entries['init.zygote32.rc']['data'].decode()
    zygote, count = re.subn(r'(^service zygote [^\n]*\n)', r'\1    disabled\n', zygote, count=1, flags=re.M)
    if count != 1: raise RuntimeError('Cannot hold zygote: service not found')
    put('init.zygote32.rc', zygote.encode())
# adbd's root label option calls setcon directly, which fails without kernel SELinux.
# Authentication remains enabled; only the unavailable root context transition is omitted.
put('init.usb.rc',entries['init.usb.rc']['data'].replace(b' --root_seclabel=u:r:su:s0',b''))
# Some bootloaders ignore header command-line additions; device permission rules still apply.
put('ueventd.rc',entries['ueventd.rc']['data']+b'\n# Lenovo board rules\n'+(device/'ueventd.mt8389.rc').read_bytes())
props=entries['default.prop']['data'].decode()
props += '\nro.b8000.legacy_kernel=true\nro.b8000.build.status=experimental-untested\npersist.sys.root_access=2\ncm.service.adb.root=1\n'
if args.public_build:
    props=re.sub(r'(?m)^(persist.sys.root_access|cm.service.adb.root)=.*\n?', '', props)
    props+='\npersist.sys.root_access=0\ncm.service.adb.root=0\n'
put('default.prop',props.encode())
key=project/'rom/adb_keys'
if args.public_build: entries.pop('adb_keys',None)
elif key.exists(): put('adb_keys',key.read_bytes(),0o100644)

def record(name,fields,data):
    fields=list(fields); fields[6]=len(data); fields[11]=len(name.encode())+1; fields[12]=0
    header=b'070701'+b''.join(('%08x'%v).encode() for v in fields)
    block=header+name.encode()+b'\0'; block+=b'\0'*((-len(block))%4)
    block+=data; block+=b'\0'*((-len(data))%4)
    return block
rebuilt=b''.join(record(name,e['fields'],e['data']) for name,e in entries.items())
rebuilt+=record('TRAILER!!!',[0]*13,b'')
compressed=gzip.compress(rebuilt,compresslevel=9,mtime=0)
ramdisk=struct.pack('<II32s472s',0x58881688,len(compressed),b'ROOTFS',b'\xff'*472)+compressed
stock_page=u32(stock,36); kernel=stock[stock_page:stock_page+u32(stock,8)]
if args.kernel_file: kernel=args.kernel_file.read_bytes()
header=bytearray(stock[:stock_page]); struct.pack_into('<I',header,8,len(kernel)); struct.pack_into('<I',header,16,len(ramdisk)); struct.pack_into('<I',header,24,0)
cmd=b'androidboot.hardware=mt8389'
header[64:576]=cmd+b'\0'*(512-len(cmd))
digest=hashlib.sha1(kernel+struct.pack('<I',len(kernel))+ramdisk+struct.pack('<I',len(ramdisk))+struct.pack('<I',0)).digest()
header[576:608]=digest+b'\0'*12
align=lambda b:b+b'\0'*((-len(b))%stock_page)
image=bytes(header)+align(kernel)+align(ramdisk)
if len(image)>6291456: raise RuntimeError('Boot image exceeds actual partition')
used=len(image); image+=b'\0'*(6291456-len(image))
(out/'boot.img').write_bytes(image)
((out/'port-boot-manifest.json') if args.output_dir else (project/'rom/port-boot-manifest.json')).write_text(json.dumps({'status':'experimental unbooted','kernelSha256':hashlib.sha256(kernel).hexdigest(),'initSha256':hashlib.sha256(entries['init']['data']).hexdigest(),'bootSha256':hashlib.sha256(image).hexdigest(),'usedBytes':used,'partitionBytes':len(image),'cmdline':cmd.decode(),'members':[{ 'name':name,'mode':oct(e['fields'][1]),'size':len(e['data']),'sha256':hashlib.sha256(e['data']).hexdigest()} for name,e in entries.items()]},indent=2))
print('Boot image packed: %d used / %d bytes' % (used,len(image)))
