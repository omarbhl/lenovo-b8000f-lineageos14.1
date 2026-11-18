# Source and external input map

This is a **binary port with source-built compatibility components**. The build
pipeline assembles a ROM from external, verified firmware plus the changes in
this repository. It is not a complete source rebuild of Android or the kernel.
The proprietary inputs remain local and must be obtained lawfully; publishing
source links is not permission to redistribute third-party blobs.

## Android compatibility source

The development checkout started from the [minimal TWRP LineageOS14.1 manifest](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_lineageos/tree/twrp-14.1),
manifest commit `6d9088e71cc3262d4286b0b73ca59bd3623741ef`. The project's
`manifests/android-source-manifest.xml` pins each actual project commit. It
contains the headers, toolchains and Android code needed for init, installd,
signapk and the two hardware wrappers; it is not a full device ROM manifest.

`scripts/fetch_sources.sh` resolves its GitHub remote to HTTPS, removes the unused
private-remote declaration, and adds the signing-tool dependency omitted from the
original minimal manifest:

- [LineageOS/android_external_conscrypt](https://github.com/LineageOS/android_external_conscrypt),
  commit `c4297341bff3fe06aa1f13c97d09c1c22a12daab`.
- `system/core` comes from [LineageOS/android_system_core](https://github.com/LineageOS/android_system_core),
  pinned by the source manifest; apply `patches/system-core-legacy.patch`.
- `frameworks/native` comes from [LineageOS/android_frameworks_native](https://github.com/LineageOS/android_frameworks_native),
  pinned by the source manifest; apply `patches/installd-no-selinux.patch`.
- Original ARM32 wrappers are maintained under `src/sensors` and `src/camera`.

The fetch script uses a local generated manifest repository with those exact
project revisions. No GitHub authentication or private source repository is needed.

## Donor userspace ZIP

Obtain **lineage-14.1-20220911-UNOFFICIAL-me173x.zip**, by superdragonpt:

- [Developer's Android File Host listing](https://androidfilehost.com/?fid=14871746926876822197).
- SHA256: `86639dfcff0f09919743f0e5a69bac09aa31d9b59ecaf5dba2c30a012cb353fb`.
- MD5 shown by the original listing: `9a8ba8d04ed262f6f374ff276dc764e5`.

Use the listing to request a fresh mirror. Mirror URLs expire and are not pinned
as permanent download locations. The SHA256 is the primary build input check;
the MD5 merely identifies the historical listing. Do not substitute another
ME173X build without re-auditing ABI and kernel compatibility.

Donor source investigation references:

- [dragonpt/android_device_asus_me173x](https://github.com/dragonpt/android_device_asus_me173x),
  inspected `asus_mm` commit `09e51c26d0c5f7343ddaf28c3d96361113d71819`.
- [dragonpt/android_kernel_asus_me173x_new](https://github.com/dragonpt/android_kernel_asus_me173x_new),
  inspected `asus_n` commit `11dd8c1c1e9adbcfc753a53fa006ef6d250fa7a1`.

These links identify the investigated code. They do not establish that the entire
donor ZIP can be recreated byte-for-byte from those repositories.

## Lenovo stock hardware inputs

The port requires B8000-F Wi-Fi stock boot and system files matching the locked
hardware blobs. These supply the original kernel/modules, paired PowerVR stack,
Lenovo camera libraries, sensor HAL, firmware and factory software defaults.
Use stock filesystem/boot images only. **Never supply userdata, account files,
NVRAM, protect/calibration partitions, preloader or another device's identity data.**

Use the pipeline's input checks and extraction manifest to reject mismatches.
A different factory version may need an intentional lockfile update and hardware
revalidation. This repository does not redistribute the development unit's stock
backup, and does not claim a verified public download of its exact stock build.

## Kernel investigation and source correspondence

- [Original-family Jelly Bean source](https://github.com/TeamYogaBlade2/android_kernel_lenovo_b8000-jellybean_osc).
  Binder/eventpoll/wait-queue source supports the narrowly documented wakeup fix.
- [Later blade10 B8000-F kernel source](https://github.com/TeamYogaBlade2/android_kernel_lenovo_b8000-new/tree/c1c9bad7cbb04c24ca6edb350ade4f722fc0235b),
  commit `c1c9bad7cbb04c24ca6edb350ade4f722fc0235b`; this is kernel3.4.67,
  not the exact3.4.5 binary used by this ROM. Its `mediatek/config/blade10`
  settings are useful hardware references, not a drop-in kernel replacement.

The build retains the acquired stock3.4.5 kernel and applies an exact-image Binder
patch. Original kernel payload SHA256 is
`affdfb176e997ef7c21dcc38aa657965c37ffccfdfd78253fe87a6dd82adf731`;
patched payload SHA256 is
`2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768`.
No exact source build of that kernel has been demonstrated. Complete corresponding
source obligations and proprietary redistribution rights remain release gates.

## Applications

Open Camera96 comes from [F-Droid](https://f-droid.org/en/packages/net.sourceforge.opencamera/),
with its [upstream source](https://opencamera.org.uk/) and F-Droid build metadata.
Use [config/apps.lock.json](../config/apps.lock.json) for each APK's exact URL and digest, not a similarly named APK from an
unverified mirror. Other optional bundled apps likewise require locked local
inputs and preserved notices/source obligations. User accounts are never inputs.

See [DEPENDENCIES.md](DEPENDENCIES.md), [BUILDING.md](BUILDING.md), and the input
lockfile for the commands and complete expected input set.
