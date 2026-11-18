#!/usr/bin/env python3
"""Download fixed, hash-verified app inputs; no credentials or private mirrors."""
import argparse,hashlib,json,pathlib,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=pathlib.Path)
    a=parser.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    for name,info in json.loads((ROOT/'config/apps.lock.json').read_text()).items():
        dest=a.output/name
        if dest.exists():
            if sha(dest)!=info['sha256']:raise SystemExit('Existing input hash mismatch: '+name)
            print('Verified cached '+name,flush=True);continue
        tmp=dest.with_suffix('.partial')
        print('Downloading '+name,flush=True)
        req=urllib.request.Request(info['url'],headers={'User-Agent':'B8000F-ROM-build/1'})
        with urllib.request.urlopen(req,timeout=90) as src,tmp.open('wb') as out:
            while True:
                data=src.read(1048576)
                if not data:break
                out.write(data)
        if sha(tmp)!=info['sha256']:
            tmp.unlink();raise SystemExit('Downloaded input hash mismatch: '+name)
        tmp.replace(dest)
if __name__=='__main__':main()
