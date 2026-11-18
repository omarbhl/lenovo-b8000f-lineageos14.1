#!/usr/bin/env python3
"""Build an isolated reinstall ZIP from the original offline image and audited fixes."""
import pathlib, shutil, subprocess, hashlib, json, zipfile
P=pathlib.Path('/mnt/e/Lenovo Tablet Project'); R=P/'rom/release-v0.2'
W=pathlib.Path('/root/b8000-build/release-v0.2'); W.mkdir(exist_ok=True); R.mkdir(exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def run(*a): subprocess.run(a,check=True)
overlay=W/'overlay'; overlay.mkdir(exist_ok=True)
files={}
for f in (P/'rom/camera-fix/overlay/system/lib').glob('*.so'): files['lib/'+f.name]=f
files.update({
 'lib/hw/sensors.default.so':P/'rom/sensor-fix/sensors.default.so',
 'lib/hw/sensors.b8000-stock.so':P/'device-inspection/full-20261118-130235/system/lib/hw/sensors.default.so',
 'lib/hw/camera.default.so':P/'rom/camera-fix/orientation/camera.default.so',
 'lib/hw/camera.b8000-original.so':P/'rom/fixes/rotation-camera/camera.default.before.so',
 'bin/installd':P/'rom/iterations/boot04/installd',
 'app/OpenCamera/OpenCamera.apk':P/'rom/fixes/rotation-camera/OpenCamera.apk',
})
props=(P/'rom/fixes/rotation-camera/build.prop').read_text()
props+='\nro.b8000.release=0.2-experimental\n'
(W/'build.prop').write_text(props); files['build.prop']=W/'build.prop'
image=W/'system.img'; shutil.copyfile(P/'rom/release/system.img',image)
commands=['mkdir /app/OpenCamera','set_inode_field /app/OpenCamera mode 040755',
 'rm /priv-app/GoogleCamera/GoogleCamera.apk','rmdir /priv-app/GoogleCamera']
manifest=[]
for i,(target,source) in enumerate(files.items()):
    staged=overlay/str(i); shutil.copyfile(source,staged)
    mode='0100755' if target=='bin/installd' else '0100644'
    parent=str(pathlib.PurePosixPath('/'+target).parent); basename=pathlib.PurePosixPath(target).name
    commands += ['cd '+parent,'rm '+basename,'write '+str(staged)+' '+basename,
      'set_inode_field '+basename+' mode '+mode,
      'set_inode_field '+basename+' uid 0','set_inode_field '+basename+' gid 0']
    manifest.append({'path':target,'sha256':sha(source),'mode':mode})
(W/'edits').write_text('\n'.join(commands)+'\n')
with (R/'filesystem-edits.log').open('w') as f:
    subprocess.run(['debugfs','-w','-f',str(W/'edits'),str(image)],stdout=f,stderr=f,check=True)
with (R/'filesystem-check.txt').open('w') as f:
    subprocess.run(['e2fsck','-fn',str(image)],stdout=f,stderr=f,check=True)
run('python3',str(P/'rom/tools/pack-port-boot.py'),'--output-dir',str(R),
 '--kernel-file',str(P/'rom/audit-binder/candidate-kernel.payload'),'--public-build')
shutil.copyfile(image,R/'system.img')
images={n:sha(R/n) for n in ['boot.img','system.img']}
(R/'IMAGE-SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in images.items()))
(R/'fix-manifest.json').write_text(json.dumps({'version':'0.2-experimental','files':manifest,'images':images,
 'security':'No pretrusted ADB key; root ADB off by default. Legacy kernel lacks SELinux. Not a production security claim.',
 'runtime':'Individual fixes confirmed on tablet. Newly assembled ZIP not yet recovery-install tested.'},indent=2))
name='B8000F-Android7.1.2-v0.2-EXPERIMENTAL'
script=(P/'rom/release/B8000F-Android7.1.2-v0.1-EXPERIMENTAL-UNTESTED-updater-script.txt').read_text()
script=script.replace('EXPERIMENTAL B8000-F Android 7.1.2 - first hardware test','B8000-F Android 7.1.2 v0.2 EXPERIMENTAL - hardware fixes')
(R/'updater-script.txt').write_text(script)
with zipfile.ZipFile(W/(name+'-unsigned.zip'),'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    z.write(P/'donor-research/lineage14-unpacked/META-INF/com/google/android/update-binary','META-INF/com/google/android/update-binary')
    z.writestr('META-INF/com/google/android/updater-script',script)
    for n in ['boot.img','system.img','IMAGE-SHA256SUMS.txt','fix-manifest.json','README.md','MANUAL-TEST-CHECKLIST.md']:
        z.write(R/n,n)
    for base in ['rom/sensor-fix','rom/camera-fix/orientation','rom/device/lenovo/b8000/rootdir','rom/init-build-device','rom/audit-binder']:
        for f in (P/base).iterdir():
            if f.is_file() and f.suffix in ['.c','.h','.sh','.mjs','.json','.md','.rc','.mk']:
                z.write(f,'source/'+f.relative_to(P/'rom').as_posix())
    for f in ['rom/iterations/boot03/init-source.patch','rom/audit-init/b8000-installd-no-selinux.patch','rom/compiled/source-manifest.xml','rom/tools/pack-port-boot.py','rom/tools/build-v02.py']:
        z.write(P/f,'source/'+pathlib.Path(f).relative_to('rom').as_posix())
keys=pathlib.Path('/root/b8000-build/release-keys'); android=pathlib.Path('/root/b8000-build/android')
run('/usr/lib/jvm/java-8-openjdk-amd64/bin/java','-Xmx2048m','-Djava.library.path='+str(android/'out/host/linux-x86/lib64'),
 '-jar',str(android/'out/host/linux-x86/framework/signapk.jar'),'-w',str(keys/'project.x509.pem'),str(keys/'project.pk8'),str(W/(name+'-unsigned.zip')),str(W/(name+'.zip')))
with (R/'signature-verification.txt').open('w') as f:
    subprocess.run(['/usr/lib/jvm/java-8-openjdk-amd64/bin/jarsigner','-verify',str(W/(name+'.zip'))],check=True,stdout=f,stderr=f)
assert 'jar verified' in (R/'signature-verification.txt').read_text()
shutil.copyfile(W/(name+'.zip'),R/(name+'.zip'))
shutil.copyfile(keys/'project.x509.pem',R/'project-test-certificate.pem')
(R/'SHA256SUMS.txt').write_text(sha(R/(name+'.zip'))+'  '+name+'.zip\n'+(R/'IMAGE-SHA256SUMS.txt').read_text())
print('Signed release ready: '+str(R/(name+'.zip')),flush=True)
