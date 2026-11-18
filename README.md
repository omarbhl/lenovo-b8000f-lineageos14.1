# Lenovo B8000-F — LineageOS 14.1 experimental port

Android 7.1.2 / API 25 for the **Lenovo Yoga Tablet 10 B8000-F Wi-Fi**.
This repository records the hardware adaptations, source patches, and tests for
a donor-based port. It is not an official Lenovo or LineageOS release, a complete
Android source tree, or a reproducible build of every component.

## Status

The development tablet's owner confirmed these functions after the fixes were installed:

- Correct display orientation and aligned touch.
- Correct automatic screen rotation.
- Front and rear camera previews upright.
- Photos captured and saved with Open Camera.

The assembled **v0.2 experimental ZIP** passed offline image/filesystem/package
checks, including its signature, hashes and installer write targets. That exact
ZIP still needs clean-install and reinstall tests in recovery. Video, sound,
connectivity, charging and endurance are not comprehensively verified.

**Security:** Android 7.1.2 is obsolete and the original kernel lacks SELinux.
The donor advertises a 2021-06-05 patch date, which does not establish equivalent
kernel coverage. This is not a modern production-secure platform. Public-build
defaults disable root ADB and omit pretrusted PC keys, but must be tested with
clean userdata. Existing user data can retain prior development settings.

## Downloads and installation

### Use at your own risk

This software is provided **AS IS**, without warranty or guarantee of any kind.
Flashing or using it may damage or brick your device, erase data, or cause loss
of functionality. You choose to install it and accept these risks. **The author,
maintainer and contributors are not responsible for device damage, data loss,
or other losses arising from its installation or use, to the fullest extent
permitted by applicable law.** Back up your data and keep recovery/rollback files
before flashing. No compatibility, reliability or security guarantee is made.

Firmware belongs in **GitHub Releases**, not Git history. While this repository
is private, v0.2 is kept as a draft release for the owner's validation. Do not
publish or mirror it until the source/license and testing gates are resolved.

- [Installation and limitations](docs/INSTALLATION.md)
- [Manual release checklist](docs/MANUAL-TEST-CHECKLIST.md)
- [Known issues and release gates](docs/KNOWN-ISSUES.md)
- [Source and build notes](docs/BUILDING.md)
- [Licensing and redistribution](docs/LICENSING.md)
- [v0.2 checksums](release/v0.2/SHA256SUMS.txt)

Install only on **B8000-F Wi-Fi**. B8000-H, B6000 and other variants are unsupported.
The installer writes boot and system, preserving userdata and calibration;
migration from stock needs a separately performed, backed-up factory reset.
Read the installation document before flashing.

## What is in this repository

| Folder | Contents |
| --- | --- |
| `src/sensors` | ARM32 wrapper correcting the Lenovo sensor mounting frame |
| `src/camera` | ARM32 wrapper correcting front/rear camera orientation |
| `patches` | Init/property-service and installd compatibility changes |
| `device` | B8000 configuration, startup rules and persistent device permissions |
| `manifests` | Pinned Android component source manifest used during development |
| `development` | Historical packaging/verification scripts requiring local inputs |
| `release/v0.2` | Checksums, fix inventory and offline validation reports |

No private signing keys, device backups, NVRAM/calibration partitions, photos,
account data, pretrusted ADB keys or firmware images are tracked here.

The Binder kernel correction is documented in [BINDER-FIX.md](docs/BINDER-FIX.md).
The release uses the acquired stock kernel binary with a reviewed one-instruction
fix, not a demonstrated source rebuild of the exact kernel.

## Credits

Lenovo/MediaTek for the original device software; TeamYogaBlade2 for the Lenovo
kernel source investigations; the ASUS ME173X LineageOS port and its contributors
for the donor; LineageOS, AOSP and TeamWin for the Android/recovery components;
Open Camera and its contributors for the working camera application.

Existing upstream copyright and license terms remain in force. See the licensing
document; no blanket license is asserted over third-party code or proprietary blobs.
