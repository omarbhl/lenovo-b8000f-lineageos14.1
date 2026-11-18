#!/bin/bash
# Build only compatibility components; Android userspace/kernel remain external inputs.
set -eo pipefail
checkout= out= jobs=4
while [ "$#" -gt 0 ]; do
  case "$1" in
    --checkout) checkout="$2"; shift 2;;
    --out) out="$2"; shift 2;;
    --jobs) jobs="$2"; shift 2;;
    *) echo 'Usage: build_components.sh --checkout PATH --out PATH [--jobs 4]' >&2; exit 2;;
  esac
done
[ -n "$checkout" ] && [ -n "$out" ] || { echo '--checkout and --out are required' >&2; exit 2; }
case "$jobs" in ''|*[!0-9]*|0) echo 'jobs must be a positive integer' >&2; exit 2;; esac
root=$(cd "$(dirname "$0")/.." && pwd)
checkout=$(realpath "$checkout"); out=$(realpath -m "$out")
[ -f "$checkout/build/envsetup.sh" ] || { echo 'Missing Android checkout; run fetch_sources.sh first.' >&2; exit 1; }
[ -d "$checkout/external/conscrypt" ] || { echo 'Missing pinned external/conscrypt; rerun fetch_sources.sh.' >&2; exit 1; }
python3 "$root/scripts/check_source_pins.py" --checkout "$checkout"
command -v python2 >/dev/null || { echo 'Python2 is required by this legacy Android build.' >&2; exit 1; }
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-8-openjdk-amd64}"
[ -x "$JAVA_HOME/bin/java" ] || { echo 'Set JAVA_HOME to a Java8 JDK.' >&2; exit 1; }
"$JAVA_HOME/bin/java" -version 2>&1 | head -1 | grep -q '"1\.8\.' || { echo 'Java8 is required.' >&2; exit 1; }
mkdir -p "$out" "$out/.host-bin" "$checkout/device/lenovo/b8000_init"
ln -sf "$(command -v python2)" "$out/.host-bin/python"
export PATH="$out/.host-bin:$JAVA_HOME/bin:$PATH"
export LC_ALL=C
apply_once() {
  local directory="$1" patch="$2"
  if git -C "$directory" apply --reverse --check "$patch" 2>/dev/null; then
    printf 'Already applied: %s\n' "$(basename "$patch")"
  elif git -C "$directory" apply --check "$patch"; then
    git -C "$directory" apply "$patch"
  else
    echo "Patch does not cleanly match $directory; do not discard local changes." >&2; exit 1
  fi
}
apply_once "$checkout/system/core" "$root/patches/system-core-legacy.patch"
apply_once "$checkout/frameworks/native" "$root/patches/installd-no-selinux.patch"
cp -a "$root/device/lenovo/b8000_init/." "$checkout/device/lenovo/b8000_init/"
cd "$checkout"
# Nougat's environment scripts are not compatible with shell nounset (-u).
source build/envsetup.sh
lunch full_b8000_init-eng
make -j"$jobs" init installd signapk
cp out/target/product/b8000_init/root/init "$out/init"
cp out/target/product/b8000_init/system/bin/installd "$out/installd"
cp out/host/linux-x86/framework/signapk.jar "$out/signapk.jar"
mkdir -p "$out/host-lib64"
find out/host/linux-x86/lib64 -maxdepth 1 -type f \( -name '*conscrypt*' -o -name '*crypto*' \) -exec cp '{}' "$out/host-lib64/" \;
export ANDROID_BUILD_TOP="$checkout"
bash "$root/src/sensors/build.sh"
bash "$root/src/camera/build.sh"
cp "$root/src/sensors/sensors.default.so" "$out/sensors.default.so"
cp "$root/src/camera/camera.default.so" "$out/camera.default.so"
python3 - "$out" <<'PY'
import hashlib,json,pathlib,sys
p=pathlib.Path(sys.argv[1]); files={}
for name in ['init','installd','signapk.jar','sensors.default.so','camera.default.so']:
    files[name]=hashlib.sha256((p/name).read_bytes()).hexdigest()
(p/'components.json').write_text(json.dumps({'kind':'locally source-built components','sha256':files},indent=2)+'\n')
PY
printf 'Built components saved to %s\n' "$out"
