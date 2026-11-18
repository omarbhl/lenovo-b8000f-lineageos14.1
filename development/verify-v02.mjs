import fs from 'node:fs';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import {Ext4} from '../../donor-research/ext4-read.mjs';
const root='rom/release-v0.2/', checks=[];
function check(name,condition){assert(condition,name);checks.push(name);}
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(root+'fix-manifest.json'));
const image=new Ext4(root+'system.img');
check('system fits original partition',fs.statSync(root+'system.img').size===1073741824&&image.totalBytes===1073741824);
for(const file of manifest.files){const n=image.lookup(file.path);check(file.path+' bytes',sha(image.data(n))===file.sha256);check(file.path+' permissions',(n.mode&0o777)===(file.path==='bin/installd'?0o755:0o644));}
check('panel mounting rotation180',image.data(image.lookup('build.prop')).toString().includes('ro.sf.hwrotation=180'));
let google=false;try{image.lookup('priv-app/GoogleCamera/GoogleCamera.apk');google=true;}catch{}
check('broken donor Camera app removed',!google);
for(const path of ['etc/adb_keys','adb_keys','data/misc/adb/adb_keys']){let found=false;try{image.lookup(path);found=true;}catch{}check('no trusted host key '+path,!found);}
image.close();
const boot=fs.readFileSync(root+'boot.img');const u=n=>boot.readUInt32LE(n),page=u(36),ks=u(8),rs=u(16);
check('boot partition size',boot.length===6291456);check('boot header',boot.toString('ascii',0,8)==='ANDROID!');
check('correct boot addresses',u(12)===0x10008000&&u(20)===0x11000000&&u(32)===0x10000100&&page===2048);
const kernel=boot.subarray(page,page+ks),pos=page+Math.ceil(ks/page)*page,ram=boot.subarray(pos,pos+rs);
check('reviewed Binder kernel',sha(kernel)==='2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768');
check('MTK ramdisk wrapper',ram.readUInt32LE(0)===0x58881688&&ram.readUInt32LE(4)===rs-512);
const int=n=>{const b=Buffer.alloc(4);b.writeUInt32LE(n);return b;};
check('boot payload identifier',boot.subarray(576,596).equals(crypto.createHash('sha1').update(kernel).update(int(ks)).update(ram).update(int(rs)).update(int(0)).digest()));
const raw=zlib.gunzipSync(ram.subarray(512)),members=new Map();
for(let p=0;p+110<=raw.length;){assert.equal(raw.toString('ascii',p,p+6),'070701');const f=i=>parseInt(raw.toString('ascii',p+6+i*8,p+14+i*8),16);const len=f(11),size=f(6),name=raw.toString('utf8',p+110,p+110+len-1);if(name==='TRAILER!!!')break;const start=Math.ceil((p+110+len)/4)*4;members.set(name,raw.subarray(start,start+size));p=Math.ceil((start+size)/4)*4;}
check('current source-built init',sha(members.get('init'))===sha(fs.readFileSync('rom/compiled/init')));
const props=members.get('default.prop').toString();
for(const line of ['ro.secure=1','ro.adb.secure=1','persist.sys.root_access=0','cm.service.adb.root=0'])check('public default '+line,props.split(/\r?\n/).includes(line));
check('no pretrusted PC public key',!members.has('adb_keys'));
check('no automatic root log collector',!members.has('b8000-capture.sh')&&!members.get('init.rc').includes(Buffer.from('b8000_capture')));
check('normal zygote startup',!/^\s*disabled\s*$/m.test(members.get('init.zygote32.rc').toString()));
check('no unsupported ADB SELinux transition',!members.get('init.usb.rc').includes(Buffer.from('--root_seclabel')));
for(const device of ['kd_camera_flashlight','mtk_jpeg','mtk_gdma','mtk_gfmt'])check('persistent permission '+device,members.get('ueventd.rc').toString().includes('/dev/'+device));
check('hardware fstab alias',members.get('fstab.mt8389').equals(members.get('fstab.mt6589')));
const script=fs.readFileSync(root+'updater-script.txt','utf8');
check('model assertion',script.includes('assert(getprop')&&script.includes('Lenovo B8000-F'));
check('system partition only',script.includes('package_extract_file("system.img", "/dev/block/mmcblk0p6")'));
check('boot staging write workaround',script.includes('assert(run_program("/sbin/dd", "if=/tmp/b8000-boot.img", "of=/dev/bootimg", "bs=2048") == "0");'));
check('sync asserted',script.includes('assert(run_program("/sbin/sync") == "0");'));
check('no automatic data/calibration wipe',!/\b(format|delete_recursive|wipe_block_device)\s*\(/.test(script));
fs.writeFileSync(root+'image-verification.json',JSON.stringify({status:'PASS',checks,zipInstalledInRecovery:false,limitations:['Public non-root ADB defaults not yet tested on a clean install.','Individual hardware fixes confirmed on tablet; assembled ZIP requires reinstall test.']},null,2));
console.log(JSON.stringify({status:'PASS',checks:checks.length}));
