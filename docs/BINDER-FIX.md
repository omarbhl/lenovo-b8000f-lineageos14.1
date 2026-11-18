# Binder first system_server kernel panic: isolated audit

## Exact mechanism

The panic tail identifies PC c0325a94 in binder_transaction; register r4=0. The decompressed kernel actually used by boot04 contains `e5943000` (`ldr r3,[r4]`) at that PC. The previous instructions are `ldr r4,[r5,#4]` and `ldr r9,[r5]`: load waitqueue entry private pointer and flags.

Original Lenovo binder.c enables RT_PRIO_INHERIT (line62) and BINDER_MONITOR (line84). The custom wake loop at lines2537-2577 assumes every wait entry's private pointer is task_struct, then reads tsk->state. That assumption is invalid for epoll. Original fs/eventpoll.c992 registers ep_poll_callback via init_waitqueue_func_entry; include/linux/wait.h104-108 explicitly sets private=NULL. binder_poll3602/3608 permits poll registration. Thus epoll on a Binder FD produces exactly the observed NULL task pointer fault.

This is not evidence for a transaction structure/security ABI mismatch. The crash occurs after transaction object handling, in notification of target waiters. ioctl c0186201 is ordinary ARM32 BINDER_WRITE_READ.

## Narrow userspace alternative

Existing cm14.1 system/core/healthd/healthd_mode_android.cpp49-59 calls setupPolling on Binder then healthd_register_event (epoll). It is the sole setupPolling caller in the downloaded frameworks/native + system source tree; other sources/binaries may also poll. A system_server batteryproperties call is a plausible trigger but recipient identity is not established by the tail. Rebuilding healthd with an ordinary Binder threadpool avoids this poll use, but introduces concurrency with main-thread BatteryMonitor and needs review. It would not fix other Binder poll users.

## Reviewed minimal kernel candidate

At Image offset0x31da94, VA c0325a94 replace e5943000 with eaffffeb: unconditional branch to c0325a48. At entry curr=r5 and flags=r9 are already loaded. The target calls curr->func(curr,TASK_INTERRUPTIBLE,0,NULL), tests callback result and WQ_FLAG_EXCLUSIVE, advances the saved next entry, and uses the original lock/unlock path. This bypasses unsafe task_struct assumptions and the associated RT scheduler adjustment. Source-level equivalent is using ordinary wake_up_interruptible(target_wait) instead of the custom RT_PRIO_INHERIT loop.

Only that loop's priority inheritance and monitor diagnostic are skipped; other Binder RT code remains. Callback semantics follow the existing generic wake loop for ordinary task and epoll callback entries. This is a targeted experimental kernel fix, not a general kernel modernization or completed ROM claim.

Files:
- stock-crash-disassembly.txt: exact offline instructions around fault and callback target.
- stock-binder.c/.h, stock-eventpoll.c, stock-wait.h: public original-family source evidence.
- stock-decompress_inflate.c: original gzip decoder; lines103-118 support FNAME.
- stock-compressed-head.S473: reads input_data_end-4 for inflated size.
- propose-patch.mjs: verifies original three instructions and produces audit-only Image copy.
- proposed-kernel.gnu.gz: GNU gzip -n -9 output from that Image.
- build-candidate.mjs: verifies stock/current payload equality and creates isolated exact-size payload.
- candidate-kernel.payload: includes original MTK512B header and ARM zImage wrapper; NOT a boot.img.
- candidate-manifest.json: hashes, sizes, offsets, CRC and verification results.

## Recompression boundary proof

Original acquired boot and saved boot04 contain byte-identical kernel payload SHA256 affdfb176e997ef7c21dcc38aa657965c37ffccfdfd78253fe87a6dd82adf731. Payload size4224696, MTK declared content4224184 after its512byte header.

Original gzip occupies kernelpayload[18984,4224640),4205656bytes. GNUgzip -n -9 patched Image is4205649bytes,7bytes smaller. Add supported FNAME flag0x08 and six ASCII bytes B8000! plus NUL after the10byte header: exactly4205656bytes. No trailing padding is used. CRC and ISIZE stay at their original offsets, and ISIZE remains8877092. The full unchanged prefix18984bytes includes MTKheader and decompressor; unchanged suffix56bytes includes original linker metadata. Wholepayload length is unchanged.

Nodegunzip roundtrip and gzip CRC/ISIZE validate the candidate. Inflated diff is exactly four bytes at31da94..31da97, representing one ARM instruction replacement. Candidate payload SHA256 2bda83c0fb373b4e9161316d66173a4a2c0c951a73404481493eef42cde1d768.

Original-family source fetched from https://raw.githubusercontent.com/TeamYogaBlade2/android_kernel_lenovo_b8000-jellybean_osc/master/kernel/ followed by drivers/staging/android/binder.c, fs/eventpoll.c, include/linux/wait.h, lib/decompress_inflate.c, arch/arm/boot/compressed/head.S. Source correlation is strongly supported by exact instruction behavior but no matching vmlinux/debugsymbols were available. No tablet commands or active release/source image changes were made in this audit.
