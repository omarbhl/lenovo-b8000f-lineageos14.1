# Lenovo B8000-F Revival — v0.3 experimental

**Known boot blocker: DO NOT INSERT A microSD CARD.** Keep the slot empty.
The storage service crashes on an unsupported SELinux operation while scanning
a card because the original kernel has no SELinux support. If boot gets stuck
with a card inserted, remove it. The SD compatibility fix is still outstanding.

About tablet now identifies the project as Lenovo B8000-F Revival, lists
Omar Bouhlal as maintainer, and links to the project's GitHub repository.
The clickable "Issues and contributions" entry invites users to report an issue
or help improve Revival on GitHub.
The change uses native Settings preferences and adds no application or service.
Existing Android/LineageOS credits and version details remain available.

Includes the v0.2.1 lock-screen/wake correction and earlier display, touch,
sensor and camera fixes. Boot animation is unchanged, as requested.
The separate Google WebView 119 user update and user-specific Updater/printing
disabling are not incorporated by this branding update. Original Settings
colours are retained; the dark preview was reverted. Logo and wallpaper are
available as separate release assets; the wallpaper is not yet installed as the
ROM default. Google services are absent; microG is untested.

The owner reports successful manual hardware checks on the development setup.
The About screen/link and wallpaper were checked on the development tablet. The repackaged
ZIP needs its own recovery installation test. This old Android/legacy-kernel
build remains experimental, with existing security and source/license limitations.

This public package refresh retains the verified v0.3 boot/system image hashes
and installer operations. It updates the packaged documentation and adds the
public project artwork/installation/known-issues documents. These offline
checks do not establish a successful recovery install of the final ZIP.

**FLASH AT YOUR OWN RISK.** Provided AS IS without warranty. The author,
maintainer and contributors are not responsible for damage, bricking, data loss
or other losses to the fullest extent permitted by applicable law.
