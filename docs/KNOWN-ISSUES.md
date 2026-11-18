# Known issues and release gates

- Public release is experimental. Android 7.1.2 and the no-SELinux kernel cannot
  meet current production security expectations.
- The full v0.2 recovery ZIP has not yet been installed as a package. Individual
  hardware fixes were applied and confirmed on one development tablet.
- Clean setup, authenticated non-root ADB defaults, dirty reinstall preserving
  app data, recovery reboot and rollback require exact-ZIP validation.
- Camera photo capture and both preview orientations are confirmed. Other modes,
  video recording, recording audio, saved metadata and long camera sessions need tests.
- The HAL enumerates an additional legacy camera entry; only the physical rear
  and front cameras are intended for use. Treat third-camera behavior as unsupported.
- Open Camera replaces a donor GoogleCamera app that crashed during panorama startup.
- Factory engineering library libacdk has an unresolved symbol against the Lenovo
  camera substitutions. It is not part of normal camera use; engineering modes
  are unsupported until this is resolved.
- Wi-Fi/Bluetooth, audio routing, microphones, charging/suspend, thermal behavior,
  media codecs and current Spotify/NewPipe/Home Assistant behavior need systematic tests.
- Kernel source correspondence, licensing notices and proprietary redistribution
  permissions must be resolved before public firmware hosting.

Record additional failures against the exact ZIP SHA-256 and installation path.
Do not claim successful tests that were only static checks.
