# Source and build notes

This is a development handoff, not a self-contained ROM build tree. Firmware,
proprietary libraries, signing keys and this tablet's backups are intentionally
absent. The historical scripts in development/ reference the original workspace
layout and must be adapted before use in a new checkout. Simply running them
here will not recreate the ZIP.

## Wrapper libraries

Use a Linux/WSL Android build checkout with the pinned headers and an ARM32 GCC4.9
toolchain plus the Android21 ARM sysroot expected by the build scripts:

```sh
export ANDROID_BUILD_TOP=/absolute/path/to/android-checkout
sh src/sensors/build.sh
sh src/camera/build.sh
```

The scripts generate untracked shared libraries next to their sources. They
depend on libc/libdl and delegate to the existing vendor HALs at these locations:

- `/system/lib/hw/sensors.b8000-stock.so`: original acquired Lenovo sensors HAL.
- `/system/lib/hw/camera.b8000-original.so`: working converted donor camera HAL.

Install the delegated libraries before their wrappers. Preserve ownership and
modes. Do not rename the wrapper itself as the original or recursively load it.

## Android compatibility modules

`manifests/android-source-manifest.xml` pins the component checkout used to build
init and installd. It is a minimal build environment, not the manifest for all
userspace binaries in the donor image.

Apply `patches/system-core-legacy.patch` from `system/core`, and
`patches/installd-no-selinux.patch` from `frameworks/native`. Copy the contents of
`device/lenovo/b8000_init` to that location in the Android checkout, then:

```sh
source build/envsetup.sh
lunch full_b8000_init-eng
make -j4 init installd
```

Use the checkout's required Java8 and Python2 build environment. The device
configuration deliberately sets `KERNEL_HAS_FINIT_MODULE := false` for kernel3.4
and opts into the B8000-only no-SELinux compatibility code. Do not enable this
path for unrelated hardware or claim it implements SELinux isolation.

## Kernel and image inputs

Read BINDER-FIX.md for the exact-image Binder patch and its tradeoffs. The target
kernel payload SHA256 after that patch is:

`2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768`

The v0.2 package was assembled offline from the verified original donor layout,
Lenovo hardware overlay, compiled compatibility modules, paired camera libraries,
wrappers, Open Camera, and patched original boot kernel. It did not copy a used
userdata filesystem into the release. The original full workspace and verified
binary inputs remain necessary to run the historical assembly scripts.

The camera hardware family must remain matched; replacing just the custom tuning
library causes interface mismatches with the donor. See release/v0.2/fix-manifest.json
for the exact installed overlay and hashes.

Use private signing keys stored outside this repository. Verify filesystem,
image sizes, boot identifier, installer partition targets, archive CRC, signature
and hashes before trying a newly assembled package. Then perform the manual
reinstall/clean-install checks on the exact signed ZIP.
