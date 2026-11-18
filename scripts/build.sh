#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
stock_boot= stock_system= donor_zip= android= work= keys= jobs=4
while [ "$#" -gt 0 ]; do
  case "$1" in
    --stock-boot) stock_boot=${2:?}; shift 2;;
    --stock-system) stock_system=${2:?}; shift 2;;
    --donor-zip) donor_zip=${2:?}; shift 2;;
    --android) android=${2:?}; shift 2;;
    --work) work=${2:?}; shift 2;;
    --keys) keys=${2:?}; shift 2;;
    --jobs) jobs=${2:?}; shift 2;;
    -h|--help) echo 'Usage: bash scripts/build.sh --stock-boot FILE --stock-system FILE --donor-zip FILE --android CHECKOUT --work EMPTY_OUTPUT_DIR --keys PRIVATE_KEY_DIR [--jobs 4]'; exit 0;;
    *) echo "Unknown argument: $1" >&2; exit 2;;
  esac
done
for name in stock_boot stock_system donor_zip android work keys; do
  if [ -z "${!name}" ]; then echo "Missing required argument: $name (see --help)" >&2; exit 2; fi
done
work=$(realpath -m "$work"); android=$(realpath "$android"); keys=$(realpath "$keys")
if [ -e "$work" ]; then echo 'Choose a new work directory; existing outputs are not overwritten.' >&2; exit 1; fi
if [ ! -f "$keys/private.pk8" ] || [ ! -f "$keys/certificate.pem" ]; then echo 'Create a local signing identity first (scripts/create_signing_key.sh).' >&2; exit 1; fi
mkdir -p "$work"
python3 "$root/scripts/prepare_inputs.py" --stock-boot "$stock_boot" --stock-system "$stock_system" --donor-zip "$donor_zip" --work "$work/inputs"
bash "$root/scripts/build_components.sh" --checkout "$android" --out "$work/components" --jobs "$jobs"
python3 "$root/scripts/fetch_apps.py" --output "$work/apps"
python3 "$root/scripts/build_rom.py" --prepared "$work/inputs" --components "$work/components" --apps "$work/apps" --output "$work/rom" --signapk "$work/components/signapk.jar" --certificate "$keys/certificate.pem" --key "$keys/private.pk8"
echo "Signed output and checksums: $work/rom"
