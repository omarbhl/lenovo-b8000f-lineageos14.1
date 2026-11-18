# Licensing and redistribution status

This repository does not establish permission to redistribute the firmware.
There is no blanket license grant over this collection. Existing upstream
copyright headers and license obligations remain applicable; a maintainer must
choose and document terms for original contributions before a public release.

Before publishing binaries:

1. Inventory included components, their copyright notices and applicable licenses.
2. Provide complete corresponding source and build/configuration/patch material
   required for GPL/LGPL components. The kernel is currently an acquired stock
   binary with a small patch; matching its exact source and toolchain remains an
   unresolved gate. This repository's records alone are not complete corresponding source.
3. Verify redistribution rights for Lenovo/MediaTek/ASUS proprietary HALs,
   firmware and other blobs. Possessing a factory image is not proof of permission.
4. Preserve the notices and source requirements for bundled applications,
   including Open Camera and any other GPL-covered components.
5. Publish build identity, hashes, limitations and installation instructions.
   Keep private signing keys, device backups and unique calibration data private.

Source investigation starting points:

- https://github.com/TeamYogaBlade2/android_kernel_lenovo_b8000-jellybean_osc
- https://github.com/TeamYogaBlade2/android_kernel_lenovo_b8000-new
- https://github.com/LineageOS/android_system_core
- https://github.com/LineageOS/android_frameworks_native
- https://opencamera.org.uk/

The pinned manifest and source files identify the component revisions used in
development. They do not confer a license on unrelated proprietary components.
