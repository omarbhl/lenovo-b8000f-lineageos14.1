# Installd no-SELinux-kernel audit

Scope: read-only source inspection and isolated patch generation. No active build files or tablet state changed by this subtask.

## Cause

`frameworks/native/cmds/installd/commands.cpp`, `restorecon_app_data_lazy()`, unconditionally calls `lgetfilecon` before and after restorecon. A kernel without SELinux cannot provide the `security.selinux` xattr, so the first call fails and the helper returns -1. `create_app_data()` then fails app directories, cache and code_cache even though directory creation and ownership may already have succeeded.

The logged `Failed before getfilecon` is consistent with this exact source path. It is not evidence that ordinary filesystem creation or user.* xattrs are unsupported.

## Minimal patch

File: `patches/installd-no-selinux.patch`. The contributor source-build helper
applies it from `frameworks/native` using `git apply` and builds the result.

Only two files change:

- `cmds/installd/Android.mk` propagates `B8000_LEGACY_NO_SELINUX=1` through common_cflags only for b8000/b8000_init eng/userdebug builds when the existing BoardConfig flag is true. Other devices/builds retain original behavior.
- `commands.cpp` includes the public SELinux API header directly and returns 0 from the lazy labeling helper if that explicit macro is enabled and `is_selinux_enabled() <= 0`.

This follows Android N libselinux's actual disabled-kernel behavior in `selinux_android_restorecon_common()`. It does not fabricate contexts, ignore labeling failures on a SELinux-enabled kernel, bypass data path/package validation, change directory uid/mode rules, or skip user cache-inode xattrs.

## Complete relevant call audit

- The only raw getfilecon/setfilecon family calls in the installd directory are the two lgetfilecon calls inside this lazy helper.
- Other commands.cpp label paths use `selinux_android_restorecon()` or `selinux_android_restorecon_pkgdir()`, which already return success when SELinux is disabled in the inspected Android N library.
- `installd.cpp` computes `selinux_enabled=(is_selinux_enabled()>0)` and gates `selinux_status_open` and reload/status checks already.
- `otapreopt.cpp` similarly guards status setup with the enabled result.
- Logging callback setup does not require a kernel SELinux filesystem and needs no bypass.
- `restorecon_app_data()` still validates package/seinfo inputs. Those validations are intentionally retained.

## Build and verification boundary

Use the existing configured product and `make installd` (or `m installd`) in the Android checkout. Output should be `out/target/product/b8000_init/system/bin/installd` for this target. The module links shared libbase, libcutils, liblog, liblogwrap and libselinux, and static libdiskusage. Its Bionic/libc++ runtime dependencies must resolve against the candidate system image; successful compilation alone does not establish target runtime compatibility.

`make-installd-patch.py` reads the active source checkout but writes snapshots, changed files and manifest only under rom/audit-init. Patch dry-run against the active source succeeded. This subtask did not perform the ARM build or execute the replacement daemon.

Source snapshots: `installd-source-commands.cpp`, `installd-source-Android.mk`. Patched files: `installd-patched/`. Hash provenance: `installd-patch-manifest.json`.
