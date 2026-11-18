#!/usr/bin/env python3
"""Check checkout HEAD revisions against the recorded component source pins."""
import argparse,pathlib,re,subprocess,xml.etree.ElementTree as E
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkout',required=True,type=pathlib.Path);a=p.parse_args()
    entries={e.get('path') or e.get('name'):e.get('revision') for e in E.parse(ROOT/'manifests/android-source-manifest.xml').getroot().findall('project')}
    entries['external/conscrypt']='c4297341bff3fe06aa1f13c97d09c1c22a12daab'
    failed=[]
    for path,expected in entries.items():
        if not expected or not re.fullmatch('[0-9a-f]{40}',expected):failed.append(path+': unpinned revision');continue
        r=subprocess.run(['git','-C',str(a.checkout/path),'rev-parse','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
        if r.returncode or r.stdout.strip()!=expected:failed.append(path+': missing or different HEAD')
    if failed:raise SystemExit('Source pin check failed:\n'+'\n'.join(failed))
    print('Source pins verified: '+str(len(entries))+' projects (local working-tree changes are not discarded)')
if __name__=='__main__':main()
