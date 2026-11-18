#!/bin/bash
# Sync exactly the recorded minimal Android component checkout; never fetch firmware.
set -euo pipefail
checkout= jobs=4 repo_tool="${REPO_TOOL:-repo}"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --checkout) checkout="$2"; shift 2;;
    --jobs) jobs="$2"; shift 2;;
    --repo) repo_tool="$2"; shift 2;;
    *) echo 'Usage: fetch_sources.sh --checkout PATH [--jobs 4] [--repo PATH]' >&2; exit 2;;
  esac
done
[ -n "$checkout" ] || { echo '--checkout is required' >&2; exit 2; }
case "$jobs" in ''|*[!0-9]*|0) echo 'jobs must be a positive integer' >&2; exit 2;; esac
root=$(cd "$(dirname "$0")/.." && pwd)
checkout=$(realpath -m "$checkout")
command -v "$repo_tool" >/dev/null || { echo 'Install Google repo first; see docs/DEPENDENCIES.md' >&2; exit 1; }
repo_tool=$(command -v "$repo_tool")
mkdir -p "$checkout"
bootstrap="$checkout/.b8000-manifest-source"
if [ -d "$checkout/.repo" ] && [ ! -f "$checkout/.b8000-source-checkout" ]; then
  echo 'Refusing to reinitialize an unrelated repo checkout. Choose a fresh --checkout.' >&2; exit 1
fi
if [ ! -d "$checkout/.repo" ] && [ -n "$(find "$checkout" -mindepth 1 -maxdepth 1 -not -name .b8000-manifest-source -print -quit)" ]; then
  echo 'Choose an empty checkout directory.' >&2; exit 1
fi
mkdir -p "$bootstrap"
python3 - "$root/manifests/android-source-manifest.xml" "$bootstrap/default.xml" <<'PY'
import sys, xml.etree.ElementTree as E
tree=E.parse(sys.argv[1]); root=tree.getroot()
# The development manifest used a GitHub-relative URL. A local bootstrap must use HTTPS.
for remote in root.findall('remote'):
    if remote.get('name')=='github': remote.set('fetch','https://github.com')
    if remote.get('name')=='private': root.remove(remote) # unused; no private remote required
if not any(p.get('path')=='external/conscrypt' for p in root.findall('project')):
    E.SubElement(root,'project',{'path':'external/conscrypt','name':'LineageOS/android_external_conscrypt',
      'remote':'github','revision':'c4297341bff3fe06aa1f13c97d09c1c22a12daab','upstream':'refs/heads/cm-14.1'})
tree.write(sys.argv[2],encoding='utf-8',xml_declaration=True)
PY
if [ ! -d "$bootstrap/.git" ]; then
  git -C "$bootstrap" init >/dev/null
  git -C "$bootstrap" symbolic-ref HEAD refs/heads/main
fi
git -C "$bootstrap" add default.xml
if ! git -C "$bootstrap" diff --cached --quiet; then
  git -C "$bootstrap" -c user.name=B8000Builder -c user.email=b8000-builder@localhost commit -m 'Pinned B8000 component manifest' >/dev/null
fi
export GIT_CONFIG_COUNT=2
export GIT_CONFIG_KEY_0=user.name GIT_CONFIG_VALUE_0=B8000Builder
export GIT_CONFIG_KEY_1=user.email GIT_CONFIG_VALUE_1=b8000-builder@localhost
cd "$checkout"
"$repo_tool" init -u "file://$bootstrap" -b main --no-clone-bundle
touch .b8000-source-checkout
"$repo_tool" sync -c --no-clone-bundle --no-tags -j"$jobs" --fail-fast
"$repo_tool" manifest -r -o "$checkout/b8000-synced-manifest.xml"
printf 'Pinned component sources synced to %s\n' "$checkout"
