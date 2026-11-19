# v0.2.1 experimental — lock-screen rotation

Prevents the lock screen from forcing the default landscape orientation while
the tablet is asleep. The lock screen follows the user's rotation preference,
so waking the tablet in its stand no longer starts upside down before unlock.
The equivalent live lock-screen setting was confirmed on the development tablet.

The system image includes `lockscreen.rot_override=true` in `/system/build.prop`.
This uses the existing LineageOS SystemUI rotation override and applies after a
factory reset. The contributor build defaults include the same property.

All v0.2 camera, touch, sensor and boot fixes are retained. Boot image, recovery
installer operations and signing identity are unchanged. This update does not
include the separate Google WebView 119 update installed on the test tablet.

The newly packaged ZIP has offline filesystem, file readback, payload checksum,
CRC and signature verification; recovery installation of this exact ZIP remains
untested. Use the manual test checklist after installation, particularly sleep,
wake, unlock and rotation lock in all four orientations. No userdata or device
calibration is included; flashing does not automatically wipe userdata.

**FLASH AT YOUR OWN RISK.** Provided AS IS, without warranty. The author,
maintainer and contributors are not responsible for damage, bricking, data loss
or other losses, to the fullest extent permitted by applicable law. Only Lenovo
B8000-F Wi-Fi is supported. This obsolete Android build is not production-secure.
