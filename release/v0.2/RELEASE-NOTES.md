# v0.2 experimental prerelease

**FLASH AT YOUR OWN RISK.** Provided AS IS with no warranty or guarantee. You
accept the risk of device damage/bricking, data loss and loss of functionality.
The author, maintainer and contributors are not responsible for damage or losses
arising from installation/use, to the fullest extent permitted by applicable law.
Back up first and keep recovery/rollback files.

Includes the confirmed panel/touch alignment, automatic sensor rotation, matched
Lenovo camera hardware/capture stack, camera mounting orientation wrappers,
persistent capture permissions, legacy startup/module/app-data compatibility,
and reviewed Binder kernel wakeup correction. Open Camera replaces the failing
donor camera application.

Root ADB is disabled by default and no pretrusted host key is bundled. The new
defaults require clean-install verification. No userdata/calibration image is
included; the installer writes boot/system only and does not automatically wipe.

Individual fixes were confirmed on one tablet. Offline image and signed-package
checks pass. The exact v0.2 ZIP still needs recovery installation, reinstall and
remaining hardware/endurance tests. See docs/ for instructions and limitations.

Firmware: B8000F-Android7.1.2-v0.2-EXPERIMENTAL.zip

SHA256: d09d865343d68cd46643873d809ecf73ba1af1a27274bf7286e576dc7e9fcbdc

Only B8000-F Wi-Fi is supported. This obsolete Android/no-SELinux platform is not
production-secure. Testing and redistribution/corresponding-source requirements
remain unresolved; public availability does not establish that those gates passed.
Do not upload this tablet's stock rollback image or inspection/backups as assets.
