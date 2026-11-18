TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_VARIANT := cortex-a7
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_SMP := true
TARGET_BOARD_PLATFORM := mt6589
TARGET_BOOTLOADER_BOARD_NAME := blade10_row_wifi
TARGET_NO_BOOTLOADER := true
TARGET_NO_KERNEL := true
TARGET_USES_64_BIT_BINDER := false
KERNEL_HAS_FINIT_MODULE := false
WITH_DEXPREOPT := false
# Applied only to this experimental legacy-kernel init build, through its audited patch.
B8000_LEGACY_NO_SELINUX := true
