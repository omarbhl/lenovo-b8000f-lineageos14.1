# Lenovo B8000-F Revival Android 7.1.2 v0.3

**microSD boot blocker: remove the microSD card and keep the slot empty.**
The current storage service crashes on an unsupported SELinux operation while
scanning a card. If startup gets stuck with a card inserted, remove the card.

**Flash at your own risk.** This software is provided AS IS, without warranty
or guarantee. Installation/use may brick or damage the tablet, erase data, or
disable functions. The author, maintainer and contributors are not responsible
for device damage, data loss or other losses arising from installation/use, to
the fullest extent permitted by applicable law. You accept these risks and must
back up your data before flashing.

For Lenovo B8000-F Wi-Fi only. This is a donor-based LineageOS 14.1 port with
source-built compatibility components and a patched original kernel. It is not
a production-secure Android release. Security patch property remains the donor's
2021-06-05 value; it does not establish equivalent coverage of the old kernel.
The kernel has no SELinux. Do not use this build for sensitive accounts or data.

## Included fixes

- Correct panel rotation and matching touchscreen behavior.
- Sensor frame correction for automatic rotation.
- Lock-screen rotation (`lockscreen.rot_override=true`) prevents an inverted screen before unlock; included in v0.2.1/v0.3 and contributor builds, but not v0.2.
- Native About tablet project, maintainer and issues/contributions GitHub entries.
- Matching Lenovo camera sensor, processing and capture libraries.
- Correct front/rear camera mounting orientation.
- Camera capture/flash device permissions that persist across reboots.
- Kernel Binder wakeup correction, legacy module loading, correct hardware
  identification and app-data creation on the no-SELinux kernel.
- Open Camera replaces the donor GoogleCamera app with its panorama startup crash.
- Existing compatible Firefox and NewPipe applications retained.

The individual fixes were installed on one B8000-F; the owner reports successful
manual hardware checks. The newly packaged ZIP still requires its own recovery
clean-install/reinstall test. Keep results for this exact ZIP using the supplied
manual checklist. Original Settings colours are retained; the separately tested
wallpaper, Google WebView 119 user update and per-user Updater/printing disabling
are not installed automatically by this ZIP.

## Installation and reinstall

1. Save important data externally. Keep a verified stock backup for YOUR tablet,
   a working B8000-F recovery and an external copy of the ROM/checksums.
2. Verify the downloaded ZIP against SHA256SUMS.txt. Use a charged battery and
   stable cable. Enter the B8000-F TWRP recovery used for this project.
3. Install B8000F-Revival-Android7.1.2-v0.3-EXPERIMENTAL.zip. The installer checks the model
   and writes only system and boot. It does not wipe userdata or write calibration,
   recovery, bootloader, NVRAM or protect partitions.
4. Existing users can first try a reinstall preserving data. Installing from stock
   requires a factory reset of app data/cache; back up before doing this. Do not
   restore Android 4 app/system settings wholesale onto Android 7.
5. Reboot; allow several minutes for first startup. Use Open Camera. Test the
   listed hardware functions before restoring accounts and installing more apps.

An installer failure must be investigated before reboot. The old MTK boot device
rejects fsync, so this installer stages boot.img in RAM, uses recovery dd, then
global sync; it checks each return code. This workflow was developed on TWRP2.6.3.0;
the exact v0.3 ZIP has not yet been installed through recovery.

This ZIP uses a project experimental certificate, not an upstream LineageOS key.
Recovery must trust that certificate to use signature verification; otherwise
verify the externally obtained SHA256 before installation. Do not describe a
checksum from the same untrusted download as proof of author identity.

## Privacy and debugging

Images are constructed offline, not copied from the running tablet. No userdata,
Wi-Fi passwords, accounts, photos, trusted PC ADB keys, private signing keys or
device calibration partitions are packaged. Authenticated ADB remains available;
root ADB is disabled by default. Users must authorize their own computers through
Android. This default differs from the development tablet. Existing userdata can
retain previous developer settings; inspect them after a reinstall.

## Public-release gates

Before distribution, pass the clean-install, reinstall, rollback and hardware
checklist on the exact signed ZIP. Publish known issues, build hash, instructions
and a specific B8000-F Wi-Fi model restriction. Do not upload this unit's original
stock rollback ZIP or inspection/backups; those are private device artifacts.

The bundled source snippets/manifests are development records, not a claim of
complete corresponding source. Public distribution requires assembling and
checking the applicable GPL/LGPL source obligations for the exact kernel and
other binaries, build instructions, licenses/notices, and redistribution rights
for Lenovo/ASUS proprietary blobs and bundled APKs. Do not publish until these
obligations and permissions are resolved. Keep private signing keys off downloads.

Original sources investigated include TeamYogaBlade2's Lenovo B8000 kernel trees,
the ASUS ME173X LineageOS donor and the pinned LineageOS source manifest packaged
under source/. The exact kernel used here is the acquired original binary with a
documented one-instruction Binder wakeup correction, not a rebuilt kernel whose
complete source correspondence has been established.

See MANUAL-TEST-CHECKLIST.md and verification reports in this folder. Functional
testing can support an experimental community release; it cannot remove obsolete
platform security limitations or justify a production-secure label.
