#!/usr/bin/env python3
"""Build an opt-in Settings-only resource preview, preserving code and resource IDs."""
import argparse,hashlib,json,pathlib,struct,subprocess,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def chunks(b,start):
    p=start
    while p<len(b):
        kind,header,size=struct.unpack_from('<HHI',b,p)
        assert 8<=header<=size and p+size<=len(b)
        yield p,kind,b[p:p+size];p+=size
    assert p==len(b)
def value(kind,data):return struct.pack('<HBBI',8,0,kind,data)
def color(s):return value(0x1c,0xff000000|int(s.lstrip('#'),16))
def reference(n):return value(1,n)
def patch_dashboard(xml):
    """Replace only the explicit light outer background; retain layout/behavior."""
    out=bytearray(xml);resources=None;changed=0
    for off,kind,chunk in chunks(xml,u16(xml,2)):
        if kind==0x180:resources=list(struct.unpack_from('<'+'I'*((len(chunk)-8)//4),chunk,8))
        if kind!=0x102:continue
        assert resources is not None
        for i in range(u16(chunk,28)):
            pos=16+u16(chunk,24)+i*u16(chunk,26);name=u32(chunk,pos+4)
            if name<len(resources) and resources[name]==0x010100d4:
                assert chunk[pos+15]==1 and u32(chunk,pos+16)==0x7f0d0041,'Unexpected dashboard background'
                struct.pack_into('<I',out,off+pos+8,0xffffffff)
                struct.pack_into('<I',out,off+pos+16,0x7f0d0017)
                changed+=1
    assert changed==1,'Expected one fixed light dashboard background'
    return bytes(out)
def patch_table(table,cfg):
    ink=color(cfg['midnightInk']);surface=color(cfg['surface']);floating=color(cfg['floatingSurface'])
    blue=color(cfg['azureBlue']);orange=color(cfg['vermilionOrange']);text=color(cfg['primaryText']);secondary=color(cfg['secondaryText'])
    common={0x01010031:ink,0x01010054:ink,0x01010036:reference(0x01060131),0x01010038:reference(0x01060141),0x0101005d:reference(0x7f10006c),0x0101009b:blue,0x01010429:secondary,0x0101042a:blue,0x01010433:surface,0x01010434:ink,0x01010435:blue,0x01010451:ink,0x01010452:ink,0x010104e0:value(0x12,0),0x010104e2:floating}
    # Native AlertController explicitly replaces panel backgrounds. Add Android
    # attributes to an existing AppCompat style, preserving its support-library
    # attributes/parent. Native and support attribute namespaces remain separate.
    # IDs/layouts below match the hash-locked framework's AlertDialog.Material.
    panel={k:reference(0x7f0d0019) for k in range(0x010100c6,0x010100d0)}
    panel.update({0x010100f2:reference(0x0109002b),0x0116003c:reference(0x010900dd),0x0116003d:reference(0x010900df),0x0116003e:reference(0x010900e1),0x0116003f:reference(0x010900dc),0x01160040:reference(0x010900c0),0x01160041:reference(0x0109002e),0x01160044:reference(0x010e00bb),0x01160045:reference(0x0105001a)})
    # Names/IDs and parent inheritance were checked against this exact APK and framework.
    styles={
        0x7f10006c:(None,panel), # direct opaque title/list/button backgrounds
        0x7f1001fb:(0x01030128,common), # SettingsBase -> dark DeviceDefault
        0x7f1001ff:(None,{0x010100d4:surface}), # action-bar widget surface
        0x7f100201:(None,{0x0101042a:blue,0x01010435:blue,0x7f01015e:surface}),
        0x7f100202:(None,{0x0101042a:blue,0x01010435:blue,0x7f01015e:surface}),
        0x7f100203:(0x0103022b,common), # preserve DialogWhenLarge behavior
        0x7f100206:(0x010302d7,{**common,0x01010031:floating,0x01010054:floating}),
        0x7f100207:(0x010302d1,{**common,0x01010031:floating,0x01010054:floating}),
        0x7f1001d7:(None,{0x01010098:orange}), # category labels only
    }
    colors={
        0x7f0d0017:ink,0x7f0d0018:ink,0x7f0d0019:floating,0x7f0d001a:floating,
        0x7f0d001b:surface,0x7f0d001c:surface,0x7f0d001d:ink,0x7f0d001e:ink,
        0x7f0d0021:blue,0x7f0d0022:blue,0x7f0d0049:orange,0x7f0d004a:text,
        0x7f0d005e:color(cfg['divider']),0x7f0d005f:text,0x7f0d0078:surface,
        0x7f0d0086:blue,0x7f0d0087:secondary,0x7f0d0088:value(0x1c,0x668e9bb0),0x7f0d0099:floating,
    }
    changed=[];seen=set();original_entries={};new_entries={}
    def patch_type(chunk,package):
        header=u16(chunk,2);typeid=chunk[8];flags=chunk[9];count=u32(chunk,12);start=u32(chunk,16)
        assert flags==0,'Only dense legacy resource tables are supported'
        offsets=list(struct.unpack_from('<'+'I'*count,chunk,header));valid=sorted(set(o for o in offsets if o!=0xffffffff))
        assert len(valid)==sum(o!=0xffffffff for o in offsets),'Aliased entry offsets unsupported'
        ends={off:(valid[i+1] if i+1<len(valid) else len(chunk)-start) for i,off in enumerate(valid)}
        data=bytearray(chunk[start:start+(valid[0] if valid else 0)]);new_offsets=[0xffffffff]*count
        for index,off in sorted(enumerate(offsets),key=lambda x:x[1]):
            if off==0xffffffff:continue
            entry=chunk[start+off:start+ends[off]];rid=(package<<24)|(typeid<<16)|index
            original_entries[(rid,chunk[20:header])]=entry
            if rid in styles:
                assert u16(entry,2)&1 and u16(entry,0)==16
                parent,n=u32(entry,8),u32(entry,12)
                items={u32(entry,16+i*12):entry[20+i*12:28+i*12] for i in range(n)}
                newparent,overrides=styles[rid]
                if rid==0x7f1001fb:assert parent==0x01030223,'Unexpected SettingsBase parent'
                items.update(overrides)
                entry=entry[:8]+struct.pack('<II',parent if newparent is None else newparent,len(items))+b''.join(struct.pack('<I',k)+v for k,v in sorted(items.items()))
                changed.append({'resource':hex(rid),'kind':'style','configuration':chunk[20:header].hex()});seen.add(rid)
            elif rid in colors:
                assert not u16(entry,2)&1 and u16(entry,0)==8
                entry=entry[:8]+colors[rid]
                changed.append({'resource':hex(rid),'kind':'color','configuration':chunk[20:header].hex()});seen.add(rid)
            new_offsets[index]=len(data);data+=entry;data+=bytes((-len(data))%4)
            new_entries[(rid,chunk[20:header])]=entry
        out=bytearray(chunk[:start]);struct.pack_into('<I',out,4,start+len(data))
        struct.pack_into('<'+'I'*count,out,header,*new_offsets)
        return bytes(out)+data
    def package(chunk):
        header=u16(chunk,2);identity=u32(chunk,8);out=bytearray(chunk[:header]);children=[]
        for off,kind,child in chunks(chunk,header):
            for field in [268,276]:
                if u32(chunk,field)==off:struct.pack_into('<I',out,field,header+sum(len(x) for x in children))
            children.append(patch_type(child,identity) if kind==0x201 and identity==0x7f else child)
        result=out+b''.join(children);struct.pack_into('<I',result,4,len(result));return result
    out=bytearray(table[:u16(table,2)])
    for off,kind,child in chunks(table,u16(table,2)):out+=package(child) if kind==0x200 else child
    struct.pack_into('<I',out,4,len(out))
    assert seen==set(styles)|set(colors),'Missing palette resource targets'
    assert original_entries.keys()==new_entries.keys(),'Resource IDs/configurations changed'
    for key,old in original_entries.items():
        if key[0] not in seen:assert old==new_entries[key],hex(key[0])
    return bytes(out),changed
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['input','framework','output','signapk','certificate','key']:p.add_argument('--'+n,type=pathlib.Path,required=True)
    p.add_argument('--java',default='java');a=p.parse_args();cfg=json.loads((ROOT/'config/settings-palette-preview.json').read_text())
    assert sha(a.input.read_bytes())==cfg['inputSha256'],'Unrecognized branded Settings APK'
    assert sha(a.framework.read_bytes())==cfg['frameworkInputSha256'],'Unrecognized framework attributes/layout IDs'
    assert sha(subprocess.check_output(['openssl','x509','-in',str(a.certificate),'-outform','DER']))==cfg['platformCertificateSha256']
    assert not a.output.exists(),'Use a fresh output APK';a.output.parent.mkdir(parents=True,exist_ok=True)
    unsigned=a.output.with_suffix('.unsigned.apk')
    with zipfile.ZipFile(a.input) as src,zipfile.ZipFile(unsigned,'w') as dst:
        patched,changes=patch_table(src.read('resources.arsc'),cfg)
        dashboard='res/layout/settings_main_dashboard.xml'
        dark_dashboard=patch_dashboard(src.read(dashboard))
        for item in src.infolist():
            if not item.filename.upper().startswith('META-INF/'):
                data=patched if item.filename=='resources.arsc' else dark_dashboard if item.filename==dashboard else src.read(item)
                dst.writestr(item,data)
    host=a.signapk.resolve().parent/'host-lib64'
    if not host.is_dir():host=a.signapk.resolve().parent.parent/'lib64'
    subprocess.run([a.java,'-Djava.library.path='+str(host),'-jar',str(a.signapk),str(a.certificate),str(a.key),str(unsigned),str(a.output)],check=True)
    with zipfile.ZipFile(a.input) as src,zipfile.ZipFile(a.output) as dst:
        assert dst.testzip() is None and len(dst.namelist())==len(set(dst.namelist()))
        members=lambda z:{n for n in z.namelist() if not n.upper().startswith('META-INF/')}
        assert members(src)==members(dst)
        for n in members(src)-{'resources.arsc',dashboard}:assert src.read(n)==dst.read(n),n
    a.output.with_suffix('.json').write_text(json.dumps({'scope':'Settings-only palette preview','inputSha256':cfg['inputSha256'],'outputSha256':sha(a.output.read_bytes()),'changedPayloads':['resources.arsc',dashboard],'dashboardOuterBackground':'Midnight Ink','codeAndBrandingPreserved':True,'resourceIdsPreserved':True,'changes':changes,'palette':cfg},indent=2)+'\n')
    print('Verified Settings-only preview: '+str(a.output)+'; resource changes: '+str(len(changes)))
if __name__=='__main__':main()
