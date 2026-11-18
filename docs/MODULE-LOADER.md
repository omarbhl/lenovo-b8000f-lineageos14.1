# Legacy module-loading findings

Read-only audit during Boot03 development. No active build or device changes by this subtask.

## Recommended fix

Set `KERNEL_HAS_FINIT_MODULE := false` in the experimental B8000 target BoardConfig.

This option already exists in LineageOS cm-14.1 `system/core/init/Android.mk`. It defines `NO_FINIT_MODULE` for init, selecting the existing implementation in **init/builtins.cpp**, not util.cpp:

```
std::string module;
if (!read_file(filename, &module)) return -1;
return init_module(&module[0], module.size(), options);
```

`do_insmod()` supplies an options string via `c_str()`, which remains a valid non-null empty string when no options were provided. This avoids the separate old-kernel EFAULT issue described below.

Linux 3.4 predates finit_module. The observed ENOSYS is therefore consistent with the current init selecting its default modern syscall path. ENOSYS is not evidence that the modules or their initialization functions ran.

## Why toybox reported Bad address

The original Jelly Bean source at `kernel/kernel/module.c` uses ordinary three-argument init_module, not a filename-based MediaTek-specific interface. Its explicit EFAULT paths include copying the supplied module byte buffer and `strndup_user(uargs, ...)`. A NULL options pointer fails the latter even when the module byte buffer is valid.

The parent observed toybox strace supplying NULL options even with a dummy argument, while the acquired stock BusyBox loader successfully loaded the same devinfo module. This isolates the loader argument behavior rather than establishing an incompatible devinfo binary.

The inspected devinfo module initialization only registers the major-196 character device and adds its cdev. It does not itself contain a usercopy operation explaining this EFAULT. Absence of devinfo/devmap is relevant to the graphics stack's efuse-read failure, but successful module loading alone does not establish graphics recovery.

Use a valid `""` options string in any custom syscall helper. Do not treat failed finit_module calls as successful or silently ignore non-ENOSYS errors.

## Build configuration

The contributor workflow uses the existing BoardConfig option in
`device/lenovo/b8000_init/BoardConfig.mk`. No alternative module-loader patch is
needed or applied. `scripts/build_components.sh` installs that configuration when
building init. Module bytes come from the hash-locked original firmware inputs.

Other loader controls: the acquired stock `/system/xbin/busybox insmod` is a useful old-environment control. Its invocation name must remain `busybox` for applet dispatch. The original stock toolbox is another possible control; neither a new driver nor forced module loading is justified merely by the modern loader's argument error.

Sources saved in this directory: `jb-kernel-module.c`, `jb-devinfo.c`, `test-kernel-module.c`, and the original init source archive. Original Jelly Bean source commit: `2b134a8e223ecf90cd0c7d7b898c230ade334a69`.
