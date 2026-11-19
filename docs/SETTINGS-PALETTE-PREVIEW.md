# Revival Settings palette preview

This optional preview was tested and then reverted at the user's request on
2026-11-19. The tablet uses the original Settings colours with Revival About
branding retained. The preview is not enabled by `build.sh` or included in the
v0.3 ZIP. SystemUI/notifications and third-party application themes are not modified.

Palette: Midnight Ink #101522, Azure Blue #2588F5, Vermilion Orange #F05A36.
Settings uses dark surfaces, state-aware light text, blue controls/icons and
orange dashboard headings. The explicitly light dashboard outer background is
changed to the dark local resource, including landscape side margins.

`scripts/preview_settings_palette.py` accepts only the SHA256-locked branded
Settings APK and matching framework in `config/settings-palette-preview.json`.
It preserves existing resource IDs/configurations, code, manifest and About
branding. It changes only `resources.arsc` and the background attribute in
`res/layout/settings_main_dashboard.xml`, then signs using the donor's existing
public AOSP platform test identity. Use the pinned build tree's test certificate
and key, not the ROM ZIP signing identity. Never publish private signing files.

Example after generating the branded Settings component:

```sh
python3 scripts/preview_settings_palette.py \
  --input /path/to/components/Settings.apk \
  --framework /path/to/donor-framework-res.apk \
  --output /path/to/new-preview/Settings.apk \
  --signapk /path/to/components/signapk.jar \
  --certificate /path/to/android/build/target/product/security/platform.x509.pem \
  --key /path/to/android/build/target/product/security/platform.pk8 \
  --java /usr/lib/jvm/java-8-openjdk-amd64/bin/java
```

The native alert controller reads separate title/content/button background
resources. Window color changes alone left the list dialog transparent. The
preview adds native Android panel attributes to an existing app style, retaining
its AppCompat parent/attributes. The native alert style points at this combined
style and uses existing dark color resources for all panels. Existing native
material list/layout resources are retained. No framework APK is modified.

References used to inspect this behavior:

- [Android material dialog style documentation](https://developer.android.com/reference/android/R.style#Theme_Material_Dialog_Alert)
- [LineageOS 14.1 native AlertController](https://github.com/LineageOS/android_frameworks_base/blob/cm-14.1/core/java/com/android/internal/app/AlertController.java)

Checked on the development tablet: main dashboard and margins, About tablet,
Display controls, Wi-Fi page, and a Sleep list dialog with readable choices,
opaque title/content/buttons and blue selected state. The one-minute timeout
was preserved. The user approved the palette while reporting the margins and
transparent dialog, which were then corrected.

Reboot testing also revealed a separate removable-SD bug: the original vold
aborts at `setexeccon` while scanning the SD disk on the non-SELinux kernel.
Removing the card let boot complete. Do not describe the SD issue as a palette
failure or a fixed storage feature. It needs its own compatibility fix and tests.

Retain the prior signed branded Settings APK for rollback. A system APK must be
replaced via recovery/root with root ownership and 0644 mode; Android rejects a
normal `/data` update of this platform-signed package. No user data reset is
required for rollback. Do not publish device logs or screenshots containing
private network/account information.
