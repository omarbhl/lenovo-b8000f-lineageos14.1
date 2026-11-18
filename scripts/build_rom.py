#!/usr/bin/env python3
"""Assemble an offline B8000-F port from prepared inputs and compiled components."""
import argparse,hashlib,json,os,pathlib,re,shutil,subprocess,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def run(*args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
def q(s):
    s=str(s)
    if '\n' in s or '\r' in s:raise ValueError('Newlines in paths are unsupported')
    return '"'+s.replace('\\','\\\\').replace('"','\\"')+'"'
def installer():
    return '''assert(getprop("ro.product.device") == "B8000" || getprop("ro.product.device") == "b8000" || getprop("ro.product.device") == "blade10_row_wifi" || getprop("ro.product.device") == "LenovoB8000-F" || getprop("ro.product.model") == "Lenovo B8000-F" || abort("Only Lenovo B8000-F Wi-Fi is supported."));
ui_print("EXPERIMENTAL B8000-F contributor build. Flash at your own risk.");
ui_print("Writes boot/system only; does not wipe user data or calibration.");
ifelse(is_mounted("/system"), unmount("/system"));
show_progress(0.90, 0);
assert(package_extract_file("system.img", "/dev/block/mmcblk0p6"));
show_progress(0.10, 0);
assert(package_extract_file("boot.img", "/tmp/b8000-boot.img"));
assert(run_program("/sbin/dd", "if=/tmp/b8000-boot.img", "of=/dev/bootimg", "bs=2048") == "0");
assert(run_program("/sbin/sync") == "0");
set_progress(1.0);
ui_print("Image writes complete.");
'''
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['prepared','components','apps','output']:p.add_argument('--'+key,required=True,type=pathlib.Path)
    p.add_argument('--signapk',type=pathlib.Path);p.add_argument('--certificate',type=pathlib.Path);p.add_argument('--key',type=pathlib.Path)
    p.add_argument('--java',default=str(pathlib.Path(os.environ['JAVA_HOME'])/'bin/java') if os.environ.get('JAVA_HOME') else 'java')
    a=p.parse_args()
    if any([a.signapk,a.certificate,a.key]) and not all([a.signapk,a.certificate,a.key]):p.error('Signing requires --signapk, --certificate and --key together')
    a.output=a.output.resolve();a.prepared=a.prepared.resolve();a.components=a.components.resolve();a.apps=a.apps.resolve()
    a.output.mkdir(parents=True,exist_ok=True)
    if any((a.output/n).exists() for n in ['system.img','boot.img','B8000F-contributor-unsigned.zip']):p.error('Use a fresh output directory; existing images will not be overwritten')
    required=[a.prepared/n for n in ['base-system.img','stock-boot.img','donor-boot.img','update-binary']]
    required += [a.components/n for n in ['init','installd','sensors.default.so','camera.default.so']]
    for f in required:
        if not f.is_file():raise SystemExit('Missing required input: '+str(f))
    appinfo=json.loads((ROOT/'config/apps.lock.json').read_text())
    for name,info in appinfo.items():
        if not (a.apps/name).is_file() or sha(a.apps/name)!=info['sha256']:raise SystemExit('App input missing/hash mismatch: '+name)
    system=a.output/'system.img';shutil.copyfile(a.prepared/'base-system.img',system)
    overlay=a.output/'overlay';shutil.copytree(a.prepared/'overlay/system',overlay)
    extras={'bin/installd':'installd','lib/hw/sensors.default.so':'sensors.default.so','lib/hw/camera.default.so':'camera.default.so'}
    for dst,src in extras.items():
        target=overlay/dst;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.components/src,target)
    for app in appinfo:
        dest=overlay/'app'/app[:-4]/app;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a.apps/app,dest)
    props=overlay/'build.prop'
    if not props.exists():raise SystemExit('Prepared overlay must contain donor build.prop')
    changes=json.loads((ROOT/'config/build-properties.json').read_text())
    lines=[x for x in props.read_text().splitlines() if x.partition('=')[0] not in changes]
    props.write_text('\n'.join(lines+[k+'='+v for k,v in changes.items()])+'\n')
    # Stage regular files only; symlink traversal could leak unrelated local data.
    files=sorted(overlay.rglob('*'))
    if any(f.is_symlink() for f in files):raise SystemExit('Symlinks in prepared overlay are forbidden')
    dirs=sorted((f for f in files if f.is_dir()),key=lambda f:(len(f.parts),str(f)))
    commands=[]
    for d in dirs:
        target='/'+d.relative_to(overlay).as_posix()
        commands+=['mkdir '+q(target),'set_inode_field '+q(target)+' mode 040755','set_inode_field '+q(target)+' uid 0','set_inode_field '+q(target)+' gid 0']
    commands+=['rm /priv-app/GoogleCamera/GoogleCamera.apk','rmdir /priv-app/GoogleCamera']
    manifest=[]
    for f in files:
        if not f.is_file():continue
        target=f.relative_to(overlay).as_posix()
        if target.startswith(('data/','misc/','lost+found/')) or f.name in ['adb_keys','adbkey','hosts.yml'] or f.suffix in ['.pk8','.pem','.key']:raise SystemExit('Forbidden overlay input: '+target)
        mode='0100755' if target.startswith(('bin/','xbin/','vendor/bin/')) else '0100644'
        parent=str(pathlib.PurePosixPath('/'+target).parent);base=f.name
        commands+=['cd '+q(parent),'rm '+q(base),'write '+q(f)+' '+q(base),'set_inode_field '+q(base)+' mode '+mode,'set_inode_field '+q(base)+' uid 0','set_inode_field '+q(base)+' gid 0']
        manifest.append({'path':target,'sha256':sha(f),'mode':mode})
    edits=a.output/'system-edits.txt';edits.write_text('\n'.join(commands)+'\n')
    with (a.output/'filesystem-edits.log').open('w') as log:run('debugfs','-w','-f',edits,system,stdout=log,stderr=log)
    with (a.output/'filesystem-check.txt').open('w') as log:run('e2fsck','-fn',system,stdout=log,stderr=log)
    # Read back every modified file, not just a filesystem-level consistency check.
    verify=a.output/'readback';verify.mkdir()
    with (a.output/'readback.log').open('w') as log:
        for i,f in enumerate(manifest):
            dest=verify/str(i);run('debugfs','-R','dump '+q('/'+f['path'])+' '+q(dest),system,stdout=log,stderr=log)
            if not dest.exists() or sha(dest)!=f['sha256']:raise SystemExit('Image file verification failed: '+f['path'])
    run(sys.executable,ROOT/'scripts/kernel.py','--stock-boot',a.prepared/'stock-boot.img','--output',a.output/'kernel.payload')
    run(sys.executable,ROOT/'scripts/boot.py','--stock-boot',a.prepared/'stock-boot.img','--donor-boot',a.prepared/'donor-boot.img','--init',a.components/'init','--device-root',ROOT/'device/lenovo/b8000/rootdir','--kernel',a.output/'kernel.payload','--output',a.output/'boot.img')
    images={n:sha(a.output/n) for n in ['boot.img','system.img']}
    report={'kind':'contributor binary port, not a full Android source build','hardware':'Lenovo B8000-F Wi-Fi only','files':manifest,'images':images,'runtimeTested':False,'security':'Old kernel without SELinux; root ADB off by default, no pretrusted host keys'}
    (a.output/'build-manifest.json').write_text(json.dumps(report,indent=2))
    sums=''.join(h+'  '+name+'\n' for name,h in images.items());(a.output/'IMAGE-SHA256SUMS.txt').write_text(sums)
    zpath=a.output/'B8000F-contributor-unsigned.zip'
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(a.prepared/'update-binary','META-INF/com/google/android/update-binary');z.writestr('META-INF/com/google/android/updater-script',installer())
        for name in ['boot.img','system.img','build-manifest.json','IMAGE-SHA256SUMS.txt']:z.write(a.output/name,name)
        z.write(ROOT/'DISCLAIMER.txt','DISCLAIMER.txt');z.write(ROOT/'docs/INSTALLATION.md','INSTALLATION.md')
        z.write(ROOT/'docs/MANUAL-TEST-CHECKLIST.md','MANUAL-TEST-CHECKLIST.md')
    if a.signapk:
        signed=a.output/'B8000F-contributor-EXPERIMENTAL.zip'
        host_lib=a.signapk.resolve().parent/'host-lib64'
        if not host_lib.is_dir():host_lib=a.signapk.resolve().parent.parent/'lib64'
        run(a.java,'-Xmx2048m','-Djava.library.path='+str(host_lib),'-jar',a.signapk.resolve(),'-w',a.certificate.resolve(),a.key.resolve(),zpath,signed)
        java_path=shutil.which(a.java) if '/' not in a.java else a.java
        jarsigner=pathlib.Path(java_path).parent/'jarsigner'
        if not jarsigner.is_file():
            jarsigner=pathlib.Path(os.environ.get('JAVA_HOME',''))/'bin/jarsigner'
        if not jarsigner.is_file():raise SystemExit('Set JAVA_HOME to the Java8 JDK so jarsigner is available')
        zpath=signed
    verify_args=[sys.executable,ROOT/'scripts/verify_package.py','--output',a.output]
    if a.signapk:verify_args+=['--jarsigner',jarsigner]
    run(*verify_args)
    print('Built '+str(zpath),flush=True)
    print('Build checks passed; recovery installation and hardware tests are still required.',flush=True)
if __name__=='__main__':main()
