#!/bin/bash
set -euo pipefail
android="${ANDROID_BUILD_TOP:?Set ANDROID_BUILD_TOP to your Android source checkout}"
out="$(cd "$(dirname "$0")" && pwd)"
sysroot="$android/prebuilts/ndk/current/platforms/android-21/arch-arm"
cc="$android/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gcc"
"$cc" --sysroot="$sysroot" -std=gnu99 -march=armv7-a -mfloat-abi=softfp -mfpu=neon -fPIC -shared -O2 -Wall -Werror \
 -I"$android/hardware/libhardware/include" -I"$android/system/core/include" \
 -Wl,-soname,camera.default.so "$out/camera_wrapper.c" -o "$out/camera.default.so" -ldl -lc
readelf -h "$out/camera.default.so" | head -15
readelf -d "$out/camera.default.so" | grep NEEDED
sha256sum "$out/camera.default.so"
