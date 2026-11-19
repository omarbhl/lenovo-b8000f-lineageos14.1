# Known issues and release gates

## microSD boot blocker

**Do not insert a microSD card. Keep the slot empty before booting this ROM.**
The original vold storage service aborts during SD partition scanning when
`setexeccon` fails on the kernel without SELinux support. This prevented boot
with the development tablet's card inserted; removing it allowed boot to finish.
The SD compatibility fix has not been implemented. Do not format a card as a
workaround; removing the card is the current recovery step.

## Test scope and remaining limitations

- Public release is experimental. Android 7.1.2 and the no-SELinux kernel cannot
  meet current production security expectations.
- The current v0.3 recovery ZIP has not yet been installed as a package. Individual
  hardware fixes were applied and confirmed on one development tablet.
- Clean setup, authenticated non-root ADB defaults, dirty reinstall preserving
  app data, recovery reboot and rollback require exact-ZIP validation.
- The owner reports passing video, audio, connectivity, charging, sleep/wake and
  other manual checks on the development installation. Earlier directly observed
  checks confirmed photos, both camera previews, orientation, About branding and
  wallpaper. Repeat these tests on the exact release ZIP; long-session results,
  camera metadata and third-camera behavior are not independently recorded.
- The HAL enumerates an additional legacy camera entry; only the physical rear
  and front cameras are intended for use. Treat third-camera behavior as unsupported.
- Open Camera replaces a donor GoogleCamera app that crashed during panorama startup.
- Factory engineering library libacdk has an unresolved symbol against the Lenovo
  camera substitutions. It is not part of normal camera use; engineering modes
  are unsupported until this is resolved.
- Broad app compatibility, thermal/endurance results and exact-release reproducibility
  still need recorded tests; dashboard use is the maintainer's main focus.
- Google services are absent and microG is untested. The separately installed
  Google WebView 119 update is not bundled; the release retains its original WebView.
- Disabling the printing apps on the development tablet left a printing-framework
  bind timeout in boot logs. This per-user cleanup is not incorporated into v0.3;
  a future ROM cleanup should remove the printing feature coherently.
- Kernel source correspondence, licensing notices and proprietary redistribution
  permissions must be resolved before public firmware hosting.

Record additional failures against the exact ZIP SHA-256 and installation path.
Do not claim successful tests that were only static checks.
