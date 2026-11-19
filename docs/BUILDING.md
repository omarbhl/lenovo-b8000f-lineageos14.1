# Build the B8000-F port

The workflow builds this repository's compatibility components from source and
assembles a flashable ROM from verified external firmware. It does **not** rebuild
all Android userspace or the exact stock kernel from source. No personal data,
private maintainer signing identity or earlier project output is needed.

## 1. Prepare the host

Use Ubuntu20.04 x86_64 or WSL2 with Java8 and Python2 for the legacy Android build,
Python3 for image tools, and at least 15GB free. Build in the Linux filesystem.
Install the packages and Google repo launcher listed in
[DEPENDENCIES.md](DEPENDENCIES.md). Clone this public repository:

```sh
git clone https://github.com/omarbhl/lenovo-b8000f-lineageos14.1.git
cd lenovo-b8000f-lineageos14.1
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

## 2. Obtain the external inputs locally

Read [SOURCES.md](SOURCES.md). Place these outside Git, for example in
`$HOME/b8000-private-inputs/`:

| File | Required input |
| --- | --- |
| stock-boot.img | Original B8000-F boot image with the exact tested kernel |
| stock-system.img | Raw ext4 Lenovo stock system image containing the locked hardware files |
| lineage-14.1-20220911-UNOFFICIAL-me173x.zip | Pinned ASUS donor ZIP from the linked developer download |

The donor/boot SHA256 and required hardware-file hashes are in
[`config/inputs.lock.json`](../config/inputs.lock.json). The stock system image
need not match one tablet's entire filesystem/slack; each selected hardware file
must match. An incompatible firmware revision fails clearly. Do not remove those
checks to make unrelated firmware pass.

A sparse factory system image must first be converted with Android's simg2img.
A recovery backup archive is not a raw ext4 image. There is no verified public
download of the exact stock build in this repository; obtain it lawfully yourself.
**Never provide userdata, accounts, NVRAM, protect/calibration, preloader or an
entire used-device disk image.** These scripts do not access or flash a tablet.

## 3. Fetch pinned component source

```sh
bash scripts/fetch_sources.sh --checkout "$HOME/b8000-android" --jobs 4
```

This generates a local manifest from the recorded commit-pinned source list,
uses public HTTPS remotes and adds the pinned signing-tool dependency. It refuses
to repurpose an unrelated checkout. Let the initial source/toolchain download
finish. Resolve missing upstream objects instead of silently switching branches.

## 4. Create your own signing identity

```sh
bash scripts/create_signing_key.sh "$HOME/b8000-private-keys"
```

Keep private.pem and private.pk8 private and backed up securely. They are not
the original release identity. The script refuses to overwrite existing keys.
Do not upload them or paste them into issues/logs/chat. The public certificate
can be shared separately when needed.

## 5. Run the complete build

Choose a **new, nonexistent** work directory for each run:

```sh
bash scripts/build.sh \
  --stock-boot "$HOME/b8000-private-inputs/stock-boot.img" \
  --stock-system "$HOME/b8000-private-inputs/stock-system.img" \
  --donor-zip "$HOME/b8000-private-inputs/lineage-14.1-20220911-UNOFFICIAL-me173x.zip" \
  --android "$HOME/b8000-android" \
  --work "$HOME/b8000-work/run01" \
  --keys "$HOME/b8000-private-keys" \
  --jobs 4
```

The build verifies the input hashes, reconstructs/resizes an offline donor copy
to 1GiB, extracts only locked hardware files, applies source patches and compiles
init/installd/signapk plus the HAL wrappers. It downloads hash-pinned Open Camera,
Firefox and NewPipe; creates the Lenovo system overlay; removes the broken donor
camera app; reconstructs the reviewed Binder kernel patch; packs normal startup
with correct device permissions and non-root authenticated ADB; and signs/verifies
the ZIP. No pretrusted computer key or used account/app data is included.

## Outputs

In `$HOME/b8000-work/run01/rom/`:

- B8000F-contributor-EXPERIMENTAL.zip: signed installation package.
- B8000F-contributor-unsigned.zip: intermediate; use the signed package.
- SHA256SUMS.txt, IMAGE-SHA256SUMS.txt, build-manifest.json.
- verification.json records the archive, installer, kernel and public-default checks.
- boot.img, system.img and local filesystem/readback/signature logs.

Keep outputs, proprietary inputs, Android checkout and keys outside Git. Review
git status before pushing; ignore rules are an aid, not permission to upload data.
Your output is **not expected to be byte-identical to v0.2**: your key, file
timestamps, component builds and contributor metadata can differ. Compare the
locked hardware/kernel identity and verification results. Do not label a new ZIP
with the published v0.2 hash. Generated images still need recovery and hardware tests.

To repeat the independent package checks later:

```sh
python3 scripts/verify_package.py --output "$HOME/b8000-work/run01/rom" \
  --jarsigner "$JAVA_HOME/bin/jarsigner"
```

## Run individual stages / reuse cached apps

```sh
python3 scripts/prepare_inputs.py --stock-boot INPUT/stock-boot.img \
  --stock-system INPUT/stock-system.img --donor-zip INPUT/donor.zip \
  --work "$HOME/b8000-work/inputs01"
bash scripts/build_components.sh --checkout "$HOME/b8000-android" \
  --out "$HOME/b8000-work/components01" --jobs 4
python3 scripts/fetch_apps.py --output "$HOME/b8000-work/apps"
python3 scripts/brand_settings.py \
  --input "$HOME/b8000-work/inputs01/overlay/system/priv-app/Settings/Settings.apk" \
  --output "$HOME/b8000-work/components01/Settings.apk" \
  --signapk "$HOME/b8000-work/components01/signapk.jar" \
  --certificate "$HOME/b8000-android/build/target/product/security/platform.x509.pem" \
  --key "$HOME/b8000-android/build/target/product/security/platform.pk8" \
  --java /usr/lib/jvm/java-8-openjdk-amd64/bin/java
python3 scripts/build_rom.py --prepared "$HOME/b8000-work/inputs01" \
  --components "$HOME/b8000-work/components01" --apps "$HOME/b8000-work/apps" \
  --output "$HOME/b8000-work/rom01" \
  --signapk "$HOME/b8000-work/components01/signapk.jar" \
  --certificate "$HOME/b8000-private-keys/certificate.pem" \
  --key "$HOME/b8000-private-keys/private.pk8"
```

Omit all three signing arguments only for a deliberately unsigned local image
build; this does not make its ZIP trusted by recovery. Local/cached app files must
match config/apps.lock.json. Versions are never substituted automatically.

## Failures and limitations

The builder adds Revival project, maintainer and clickable source preferences to
the existing native About tablet screen. `config/branding.json` records the input
Settings APK and platform certificate hashes. The patch changes only
`res/xml/device_info_settings.xml`; existing code, other resource payloads and
resource IDs are preserved and checked. It uses the donor's existing public AOSP
test platform identity from the pinned Android build tree, which is distinct from
your private ROM ZIP signing identity. No keys or prebuilt Settings APK are
tracked. OpenSSL is required for certificate identity checks. Existing LineageOS
and Android credits/version information remain intact. Boot animation is unchanged.

- Keep original firmware unchanged. Use fresh work directories after failures.
- prepare-inputs.log identifies hash, resize and hardware extraction errors.
- Patch failures require comparing pinned source with local edits; the builder
  never resets or discards a contributor's changes.
- filesystem-edits.log and filesystem-check.txt diagnose assembly problems.
  Every modified file is read back and hashed because debugfs can fail silently.
- The wrappers require their locked delegated originals; see SOURCES.md. Another
  stock kernel/firmware revision is a new porting task, not a hash-check bypass.
- The exact stock kernel has no demonstrated source rebuild. Source/license
  obligations and proprietary redistribution rights remain public-release gates.
- Passing build checks does not establish a modern secure system or complete the
  manual installation/hardware/endurance checklist.
