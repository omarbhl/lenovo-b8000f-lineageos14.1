#!/usr/bin/env python3
import pathlib,hashlib,json,zipfile,re
R=pathlib.Path('/mnt/e/Lenovo Tablet Project/rom/release-v0.2')
name='B8000F-Android7.1.2-v0.2-EXPERIMENTAL.zip'
def digest(f):
    h=hashlib.sha256()
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
manifest=json.loads((R/'fix-manifest.json').read_text()); checks=[]
def check(n,b):
    assert b,n
    checks.append(n)
with zipfile.ZipFile(R/name) as z:
    names=z.namelist()
    check('no duplicate entries',len(names)==len(set(names)))
    check('ZIP CRC integrity',z.testzip() is None)
    check('no private keys or device partition backups',not any(pathlib.PurePosixPath(n).name.lower() in ['adb_keys','adbkey','nvram.img','protect_f.img','protect_s.img','preloader.bin','emmc-prefix.bin'] or n.endswith(('.pk8','project.pem')) for n in names))
    for n,expected in manifest['images'].items():
        with z.open(n) as f: actual=digest(f)
        check(n+' packaged image hash',actual==expected)
    check('current manifest',json.loads(z.read('fix-manifest.json'))==manifest)
    check('current installer',z.read('META-INF/com/google/android/updater-script')==(R/'updater-script.txt').read_bytes())
    script=z.read('META-INF/com/google/android/updater-script').decode()
    check('only intended extraction targets',re.findall(r'package_extract_file\("([^"]+)",\s*"([^"]+)"\)',script)==[('system.img','/dev/block/mmcblk0p6'),('boot.img','/tmp/b8000-boot.img')])
    allowed={'assert','getprop','abort','ui_print','ifelse','is_mounted','unmount','show_progress','package_extract_file','run_program','set_progress'}
    check('installer operation allowlist',set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',script))<=allowed)
    check('documentation included',all(n in names for n in ['README.md','MANUAL-TEST-CHECKLIST.md']))
    check('source records included',any(n.endswith('sensors_wrapper.c') for n in names) and any(n.endswith('camera_wrapper.c') for n in names))
with (R/name).open('rb') as f: actual=digest(f)
check('external ZIP checksum',actual in (R/'SHA256SUMS.txt').read_text())
check('signature verified','jar verified' in (R/'signature-verification.txt').read_text())
report={'status':'PASS','checks':checks,'zipSha256':actual,'zipBytes':(R/name).stat().st_size,
 'recoveryInstallTested':False,'productionReady':False,
 'remaining':['Test this exact ZIP through recovery, including clean install and reinstall.','Verify public ADB authorization/defaults on clean userdata.','Complete manual hardware/endurance checklist.','Resolve security limitations, licenses and complete corresponding source before public distribution.']}
(R/'package-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
