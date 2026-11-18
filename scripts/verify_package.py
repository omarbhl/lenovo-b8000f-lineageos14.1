#!/usr/bin/env python3
"""Verify a contributor output independently, optionally including its signature."""
import argparse,gzip,hashlib,json,pathlib,re,subprocess,zipfile
def sha(f):
    h=hashlib.sha256()
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=pathlib.Path);p.add_argument('--jarsigner',type=pathlib.Path)
    a=p.parse_args();root=a.output.resolve();signed=root/'B8000F-contributor-EXPERIMENTAL.zip'
    package=signed if signed.exists() else root/'B8000F-contributor-unsigned.zip'
    manifest=json.loads((root/'build-manifest.json').read_text());checks=[]
    def check(n,b):
        if not b:raise SystemExit('Verification failed: '+n)
        checks.append(n)
    check('system partition size',(root/'system.img').stat().st_size==1073741824)
    boot=(root/'boot.img').read_bytes();check('boot partition size',len(boot)==6291456)
    check('boot magic',boot[:8]==b'ANDROID!')
    u=lambda n:int.from_bytes(boot[n:n+4],'little');page=u(36);ks=u(8);rs=u(16)
    kernel=boot[page:page+ks];rampos=page+((ks+page-1)//page)*page;ram=boot[rampos:rampos+rs]
    check('reviewed Binder kernel',hashlib.sha256(kernel).hexdigest()=='2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768')
    i=lambda n:n.to_bytes(4,'little')
    check('boot identifier',boot[576:596]==hashlib.sha1(kernel+i(ks)+ram+i(rs)+i(0)).digest())
    raw=gzip.decompress(ram[512:]);members={};pos=0
    while pos+110<=len(raw):
        check('CPIO header '+str(pos),raw[pos:pos+6]==b'070701')
        f=lambda n:int(raw[pos+6+n*8:pos+14+n*8],16)
        size=f(6);length=f(11);name=raw[pos+110:pos+110+length-1].decode()
        if name=='TRAILER!!!':break
        start=(pos+110+length+3)&~3;members[name]=raw[start:start+size];pos=(start+size+3)&~3
    check('no trusted host key','adb_keys' not in members)
    props=members['default.prop'].decode().splitlines()
    for value in ['ro.secure=1','ro.adb.secure=1','persist.sys.root_access=0','cm.service.adb.root=0']:check(value,value in props)
    check('no automatic diagnostic logger','b8000-capture.sh' not in members)
    check('normal zygote startup',not re.search(r'^\s*disabled\s*$',members['init.zygote32.rc'].decode(),re.M))
    with zipfile.ZipFile(package) as z:
        names=z.namelist();check('no duplicate ZIP entries',len(names)==len(set(names)))
        check('ZIP CRCs',z.testzip() is None)
        check('only documented ZIP entries',set(names)=={'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script','boot.img','system.img','build-manifest.json','IMAGE-SHA256SUMS.txt','DISCLAIMER.txt','INSTALLATION.md','MANUAL-TEST-CHECKLIST.md','META-INF/MANIFEST.MF','META-INF/CERT.SF','META-INF/CERT.RSA','META-INF/com/android/otacert'} if package==signed else set(names)=={'META-INF/com/google/android/update-binary','META-INF/com/google/android/updater-script','boot.img','system.img','build-manifest.json','IMAGE-SHA256SUMS.txt','DISCLAIMER.txt','INSTALLATION.md','MANUAL-TEST-CHECKLIST.md'})
        for n,expected in manifest['images'].items():
            with z.open(n) as f:check(n+' payload SHA256',sha(f)==expected)
            with (root/n).open('rb') as f:check(n+' local SHA256',sha(f)==expected)
        check('current manifest',json.loads(z.read('build-manifest.json'))==manifest)
        script=z.read('META-INF/com/google/android/updater-script').decode()
        check('only boot/system extraction',re.findall(r'package_extract_file\("([^"]+)",\s*"([^"]+)"\)',script)==[('system.img','/dev/block/mmcblk0p6'),('boot.img','/tmp/b8000-boot.img')])
        calls=re.findall(r'run_program\(([^)]*)\)',script)
        check('only checked recovery dd/sync',calls==['"/sbin/dd", "if=/tmp/b8000-boot.img", "of=/dev/bootimg", "bs=2048"','"/sbin/sync"'] and all('assert(run_program('+c+') == "0");' in script for c in calls))
        check('model assertion','assert(getprop' in script and 'Lenovo B8000-F' in script)
        allowed={'assert','getprop','abort','ui_print','ifelse','is_mounted','unmount','show_progress','package_extract_file','run_program','set_progress'}
        check('installer operation allowlist',set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',script))<=allowed)
    if a.jarsigner:
        check('signed package exists',package==signed)
        r=subprocess.run([str(a.jarsigner),'-verify',str(package)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True)
        check('signature verification','jar verified' in r.stdout);(root/'signature-verification.txt').write_text(r.stdout)
    with package.open('rb') as f:package_sha=sha(f)
    (root/'SHA256SUMS.txt').write_text(package_sha+'  '+package.name+'\n'+''.join(v+'  '+k+'\n' for k,v in manifest['images'].items()))
    report={'status':'PASS','checks':checks,'packageSha256':package_sha,'signed':package==signed,'signatureVerified':bool(a.jarsigner),'runtimeTested':False}
    (root/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
if __name__=='__main__':main()
