#!/usr/bin/env python3
"""Add native About-tablet preferences without changing Settings code/resources IDs.

Only the pinned donor APK is accepted. No binary APK or private key is published.
The existing Settings certificate must match the supplied platform certificate.
"""
import argparse, hashlib, json, pathlib, struct, subprocess, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
NONE=0xffffffff
def sha(data):return hashlib.sha256(data).hexdigest()
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def chunks(b,start=8):
    pos=start
    while pos<len(b):
        kind,header,size=struct.unpack_from('<HHI',b,pos)
        if size<header or size<8 or pos+size>len(b):raise ValueError('Invalid XML chunk')
        yield kind,b[pos:pos+size]
        pos+=size
    assert pos==len(b)
def length8(b,p):
    a=b[p];return (((a&127)<<8)|b[p+1],p+2) if a&128 else (a,p+1)
def length16(b,p):
    a=struct.unpack_from('<H',b,p)[0]
    return (((a&32767)<<16)|struct.unpack_from('<H',b,p+2)[0],p+4) if a&32768 else (a,p+2)
def strings(pool):
    count,styles,flags,start,end=struct.unpack_from('<IIIII',pool,8)
    assert struct.unpack_from('<H',pool,2)[0]==28
    result=[]
    for i in range(count):
        pos=start+u32(pool,28+i*4)
        if flags&256:
            _,pos=length8(pool,pos);n,pos=length8(pool,pos)
            result.append(pool[pos:pos+n].decode('utf8'))
        else:
            n,pos=length16(pool,pos);result.append(pool[pos:pos+2*n].decode('utf-16le'))
    return result
def extend_pool(pool,added):
    count,styles,flags,start,end=struct.unpack_from('<IIIII',pool,8)
    offsets=list(struct.unpack_from('<'+'I'*count,pool,28))
    styleoffsets=pool[28+count*4:28+(count+styles)*4]
    data=bytearray(pool[start:end if end else len(pool)])
    def len8(n):return bytes([n]) if n<128 else bytes([(n>>8)|128,n&255])
    for value in added:
        offsets.append(len(data));raw=value.encode('utf-16le')
        if flags&256:
            utf=value.encode('utf8');data+=len8(len(raw)//2)+len8(len(utf))+utf+b'\0'
        else:data+=struct.pack('<H',len(raw)//2)+raw+b'\0\0'
    data+=bytes((-len(data))%4)
    newstart=28+4*len(offsets)+4*styles
    newend=newstart+len(data) if end else 0
    styledata=pool[end:] if end else b''
    result=struct.pack('<HHIIIIII',1,28,newstart+len(data)+len(styledata),len(offsets),styles,flags&~1,newstart,newend)
    result+=struct.pack('<'+'I'*len(offsets),*offsets)+styleoffsets+data+styledata
    assert strings(result)==strings(pool)+added
    return result
def patch_xml(xml,config):
    assert xml[:4]==b'\x03\0\x08\0' and u32(xml,4)==len(xml)
    parts=list(chunks(xml));pool=next(b for k,b in parts if k==1);old=strings(pool);allstrings=old[:]
    def idx(s):
        if s not in allstrings:allstrings.append(s)
        return allstrings.index(s)
    resources=next(b for k,b in parts if k==0x180)
    ids=list(struct.unpack_from('<'+'I'*((len(resources)-8)//4),resources,8))
    expected={'title':0x010101e1,'summary':0x010101e9,'key':0x010101e8,'selectable':0x010101e6,'action':0x0101002d,'data':0x0101002e}
    for name,rid in expected.items():assert ids[old.index(name)]==rid,name
    ns=idx('http://schemas.android.com/apk/res/android')
    def attr(name,value):
        key=idx(name)
        if isinstance(value,bool):raw=NONE;kind=0x12;data=0xffffffff if value else 0
        else:raw=idx(value);kind=3;data=raw
        return struct.pack('<IIIHBBI',ns,key,raw,8,0,kind,data)
    def start(name,attrs):
        # Android's binary attribute lookup expects framework resource IDs sorted.
        values=b''.join(attr(k,v) for k,v in sorted(attrs.items(),key=lambda kv:expected[kv[0]]))
        return struct.pack('<HHIII',0x102,16,36+len(values),1,NONE)+struct.pack('<IIHHHHHH',NONE,idx(name),20,20,len(attrs),0,0,0)+values
    def end(name):return struct.pack('<HHIIIII',0x103,16,24,1,NONE,NONE,idx(name))
    nodes=start('PreferenceCategory',{'title':'Revival project','key':'revival_project_group'})
    for key,title,value in [('project','Project',config['project']),('maintainer','Maintainer',config['maintainer'])]:
        nodes+=start('Preference',{'key':'revival_'+key,'title':title,'summary':value,'selectable':False})+end('Preference')
    nodes+=start('Preference',{'key':'revival_source','title':config['repositoryTitle'],'summary':config['repositorySummary']})
    nodes+=start('intent',{'action':'android.intent.action.VIEW','data':config['repository']})+end('intent')+end('Preference')+end('PreferenceCategory')
    patched=[];inserted=False
    for kind,data in parts:
        if kind==1:data=extend_pool(data,allstrings[len(old):])
        patched.append(data)
        if kind==0x102 and not inserted:
            assert old[u32(data,20)]=='PreferenceScreen'
            patched.append(nodes);inserted=True
    assert inserted
    body=b''.join(patched);result=struct.pack('<HHI',3,8,len(body)+8)+body
    # Original XML nodes remain byte-for-byte intact. Only append strings/new nodes.
    originals=[b for k,b in parts if k not in [1]]
    after=[b for k,b in chunks(result) if k!=1]
    cursor=0
    for b in after:
        if cursor<len(originals) and b==originals[cursor]:cursor+=1
    assert cursor==len(originals)
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['input','output','signapk','certificate','key']:p.add_argument('--'+name,required=True,type=pathlib.Path)
    p.add_argument('--java',default='java');a=p.parse_args()
    cfg=json.loads((ROOT/'config/branding.json').read_text())
    assert sha(a.input.read_bytes())==cfg['settingsInputSha256'],'Unrecognized Settings APK'
    der=subprocess.check_output(['openssl','x509','-in',str(a.certificate),'-outform','DER'])
    assert sha(der)==cfg['platformCertificateSha256'],'Platform signer mismatch'
    if a.output.exists():raise SystemExit('Choose a new output APK')
    a.output.parent.mkdir(parents=True,exist_ok=True);unsigned=a.output.with_suffix('.unsigned.apk')
    entry='res/xml/device_info_settings.xml'
    with zipfile.ZipFile(a.input) as src,zipfile.ZipFile(unsigned,'w') as dst:
        for item in src.infolist():
            if item.filename.upper().startswith('META-INF/'):continue
            dst.writestr(item,patch_xml(src.read(item),cfg) if item.filename==entry else src.read(item))
    host=a.signapk.resolve().parent/'host-lib64'
    if not host.is_dir():host=a.signapk.resolve().parent.parent/'lib64'
    subprocess.run([a.java,'-Djava.library.path='+str(host),'-jar',str(a.signapk),str(a.certificate),str(a.key),str(unsigned),str(a.output)],check=True)
    with zipfile.ZipFile(a.input) as src,zipfile.ZipFile(a.output) as dst:
        assert dst.testzip() is None
        assert len(dst.namelist())==len(set(dst.namelist()))
        assert {n for n in src.namelist() if not n.upper().startswith('META-INF/')}=={n for n in dst.namelist() if not n.upper().startswith('META-INF/')}
        for n in src.namelist():
            if n!=entry and not n.upper().startswith('META-INF/'):assert src.read(n)==dst.read(n),n
    a.output.with_suffix('.json').write_text(json.dumps({'project':cfg['project'],'maintainer':cfg['maintainer'],'source':cfg['repository'],'originalSha256':cfg['settingsInputSha256'],'apkSha256':sha(a.output.read_bytes()),'onlyChangedPayload':entry,'existingCodeAndResourcesPreserved':True,'bootAnimationChanged':False},indent=2)+'\n')
    print('Verified resource-only branding: '+str(a.output))
if __name__=='__main__':main()
