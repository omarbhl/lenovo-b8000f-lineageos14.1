# B8000-F v0.2 manual release checklist

This checklist is for the **Lenovo B8000-F Wi-Fi** experimental Android 7.1.2 port. Do not use it to approve B8000-H, B6000, or other variants.

The screen, touch alignment, auto-rotation, front/rear preview orientation, and photo saving were confirmed on the development tablet. Reinstallation of this release ZIP and the remaining checks below need their own results. A checked box means you actually performed the test on this exact build.

Passing functional tests supports an **experimental community release**. It does not make Android 7.1.2 or a kernel without SELinux a modern, secure production platform. Publish that limitation prominently; do not describe this ROM as receiving current security updates or suitable for security-sensitive use.

## Record every test run

- Build filename and SHA-256:
- Tablet model, storage size, hardware revision if known:
- Recovery name/version:
- Previous ROM and clean-install/upgrade path:
- Date, tester, battery condition, connected accessories:
- Test result: PASS / FAIL / NOT TESTED; steps, expected/actual behavior, logs:

Keep a failure list. A crash, restart, corrupted photo/file, lost calibration, failed boot, or data loss blocks release until resolved or explicitly scoped out in the release notes. Repeat affected tests after a fix and run a short boot, touch, Wi-Fi, audio, camera, and charging regression check.

## 1. Installation, upgrade, and recovery

**Back up personal files and verify your recovery/rollback files first. A clean installation and factory reset erase app data. Copy backups off the tablet. Never distribute or restore another tablet's calibration partitions.**

- [ ] Verify the downloaded ZIP against the published SHA-256 before flashing. Recovery accepts the intended package and the installer reports success.
- [ ] Clean install on a backed-up B8000-F, following the release instructions exactly. First boot reaches usable setup/home; record the time. Do not interrupt app optimization simply because it is slow.
- [ ] Complete setup without a Google account or Google Play Services. Keyboard, time zone, language, navigation, and Settings work.
- [ ] Reinstall the same ZIP over itself without a wipe. Installed apps, their data, Wi-Fi settings, and personal files remain accessible; all hardware fixes remain.
- [ ] Upgrade from the previous supported project build without a wipe, if that path is advertised. Verify app data and files against the backup. If unsupported, state that clearly instead of claiming it works.
- [ ] Perform 10 normal reboots and 5 complete power-off/power-on cycles. Every boot reaches home without manual ADB commands.
- [ ] Reboot into recovery and back into Android. Recovery remains usable after installation.
- [ ] On the backed-up test tablet, exercise the documented stock rollback. Stock boots, touch works, and this unit's calibration/connectivity remains intact. Reinstall this build and repeat the basic hardware check.
- [ ] Factory reset this build and repeat first setup. The ROM's camera and sensor fixes survive; Open Camera is available without manually reinstalling dependencies.
- [ ] Check installer logs: only intended boot/system partitions are written. There are no writes to preloader, NVRAM, protect/calibration, recovery, or userdata unless a separately documented user action requests them.

## 2. Display, touch, and sensors

- [ ] At boot, lock screen, home, Settings, keyboard, and recovery, verify the expected display orientation. Document any boot-logo/recovery orientation difference.
- [ ] Drag an icon/finger across a grid covering all four corners, edges, and center. Touch follows the same location without mirrored axes, offsets, dead strips, or phantom taps.
- [ ] Test two-finger pinch/zoom, scrolling, long press, and dragging for 5 minutes. Test while charging as well.
- [ ] Enable auto-rotation and turn through all four physical orientations 10 times in Settings, browser, and camera. Rotation follows the right direction and touch remains aligned. If an app intentionally locks an orientation, test another app.
- [ ] Disable auto-rotation, rotate the tablet, then re-enable it. Locking/unlocking and sleep/wake preserve correct behavior.
- [ ] Move brightness from minimum to maximum. Test automatic brightness in a dark and a bright room. No flickering, unintended black screen, or stuck brightness.
- [ ] Check compass/direction in an appropriate app, if advertised. Do not infer compass correctness from working auto-rotation.
- [ ] Test the tablet stand/cover in its common positions; opening/closing or moving it should not create unexplained sleep/rotation loops.

## 3. Camera and media

Use **Open Camera**. The donor Google Camera app has a known panorama/startup problem and must not be presented as the supported camera app.

- [ ] For both front and rear cameras, open preview 10 times, switch cameras repeatedly, and return after sleep/wake. Preview is upright, responds to movement, and never remains black or freezes.
- [ ] Take at least 10 photos per camera in portrait and landscape, including bright and dim scenes. Verify the saved JPEGs in the gallery **and on another computer**: correct orientation, colors, dimensions, readable image, and no corruption.
- [ ] Test supported focus modes, exposure compensation, zoom, and each advertised resolution. Do not advertise unsupported modes simply because a menu lists them.
- [ ] Record 5 minutes of video per camera at the intended default resolution, then test other advertised resolutions. Replay on the tablet and a computer; check sound, orientation, frame delivery, and audio/video synchronization.
- [ ] Open another app that uses the camera, then return to Open Camera. Busy-camera handling recovers after the other app closes.
- [ ] Deny camera/microphone/storage permissions, then grant them. The app explains the missing permission and recovers without a reboot.
- [ ] Test low storage using a safe amount of test data. Capture fails gracefully when storage is insufficient and works after space is freed.
- [ ] Play local H.264 video and music for 30 minutes. Check speaker sound, pause/resume, seeking, volume buttons, and screen rotation.
- [ ] Test speaker and headphone output, headphone insertion/removal, microphone recording, and recorded audio playback. Test Bluetooth audio if advertised.

## 4. Connectivity, storage, and daily apps

- [ ] Connect to at least two Wi-Fi networks using supported security modes. Test saved-password reconnect after reboot, airplane mode, and sleep. Record any unsupported band/security mode.
- [ ] Browse/download for 30 minutes, then leave Wi-Fi connected overnight. Verify reconnect after access-point restart and moving out of range/back.
- [ ] Test Bluetooth pairing, reconnect, and file/audio use with available accessories if Bluetooth is advertised. Test GPS separately if advertised.
- [ ] Copy a large test file through USB/MTP in both directions and compare hashes on the computer. Internal storage remains visible after reboot.
- [ ] If a microSD card is supported/advertised, test insertion, reading, writing, safe removal, reinsertion, and reboot with the card present. Back up the card first.
- [ ] Install, update, launch, and uninstall several compatible apps. Verify app data survives a reboot and a same-version ROM reinstall.
- [ ] **Spotify:** record the exact app version/source; sign in, browse, and play for 30 minutes with the screen on and off. Test headphones/Bluetooth if used. Confirm pause/resume after opening another app.
- [ ] **YouTube use:** record the actual supported client/version, such as NewPipe. Play several videos for 30 minutes at realistic resolutions, seek, rotate, and test sound. Do not claim current official YouTube support merely because an alternative works.
- [ ] **Home Assistant:** record app/browser/WebView and server versions. Load the actual dashboard, refresh it, operate test controls, and reconnect after sleep/network loss. Only test real controls when their effects are safe.
- [ ] Test notifications, keyboard entry, browser HTTPS, date/time synchronization, downloads, clipboard, and opening downloaded files.

## 5. Sleep, charging, heat, and endurance

- [ ] Perform 20 screen-off/wake cycles using the power button, with Wi-Fi on and off. No blank-screen lockup, reboot, or lost touch.
- [ ] Leave asleep for 8 hours and then 24 hours. Record battery percentage before/after, reconnect behavior, and whether the tablet wakes normally.
- [ ] Charge with a suitable wall charger and separately with PC USB. Record percentage/voltage behavior, charging indication, and charging while asleep. Test disconnect/reconnect and boot while plugged in.
- [ ] On the supervised test unit, check low-battery warning and normal shutdown/recharge behavior. Do not repeatedly deep-discharge an aged battery to satisfy a checklist.
- [ ] Play video for 2 hours while monitoring touch, sound, temperature, and battery. Stop if the tablet/battery becomes abnormally hot or shows swelling; that is a hardware problem to resolve.
- [ ] Use browser, camera, music, Home Assistant, and Settings in succession for 30 minutes. Under low RAM, apps may reload; the system must stay responsive without boot loops or corrupted data.
- [ ] Use the tablet normally for at least 2 full days. Record every restart, freeze, battery anomaly, camera failure, and connection drop rather than relying on a single successful session.

## 6. Public-release gates

These are release checks in addition to manual hardware tests.

- [ ] The public ZIP contains no personal files, accounts, Wi-Fi passwords, logs/photos, ADB authorized keys, private signing keys, or this device's unique NVRAM/protect/calibration images. Build images from controlled inputs rather than dumping a used `/data` partition.
- [ ] ADB root is disabled by default, debugging access requires the user's authorization, and no debugging service listens on a network interface by default. Test with a previously unauthorized computer and after factory reset. Document any remaining development/root capability.
- [ ] State the actual Android version, security patch date, SELinux status, signing status, supported hardware variant, installation/upgrade/reset behavior, and known limitations. Do not relabel old security patches as current.
- [ ] Publish the ZIP hash, installation instructions, tested recovery version, rollback instructions, changelog, known issues, and test results. Label untested features plainly.
- [ ] Audit all included components' redistribution terms. Provide required copyright/license notices and corresponding source, build instructions, configurations, and modifications for GPL-covered components as applicable. Include the exact kernel base and Binder modification, init/installd patches, and HAL wrapper sources. Verify permission to redistribute proprietary Lenovo/ASUS blobs and bundled apps before hosting them publicly.
- [ ] Protect the release signing private key, publish the verification fingerprint, and define how later updates are signed. Do not put private keys in the repository or ZIP.
- [ ] Obtain results from another B8000-F unit if possible. A single tablet does not establish compatibility with all panel/camera/storage revisions; state the tested unit count.
- [ ] Resolve all release-blocking failures and publish remaining limitations. Release as experimental while the platform's security limitations remain.

## Suggested result table

| Area | Build SHA-256 | Clean/upgrade | Result | Evidence / issue |
| --- | --- | --- | --- | --- |
| Installation/reinstall/rollback | | | | |
| Display/touch/auto-rotation | | | | |
| Front/rear photo and video | | | | |
| Audio/microphone | | | | |
| Wi-Fi/Bluetooth/storage | | | | |
| Spotify/video/Home Assistant | | | | |
| Sleep/charging/endurance | | | | |
| Public-release gates | | | | |
