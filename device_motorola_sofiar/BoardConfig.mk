#
# BoardConfig.mk за Motorola Moto G8 Power (sofiar) XT2041-3 - TWRP
#
# Всички стойности, маркирани "РЕАЛНИ ДАННИ", са извлечени директно
# от stock firmware (build RETEU 11 RPES31.Q4U-47-35-12).
# Виж reference/device-findings.md за пълния произход на данните.
# Стойности, маркирани "TODO", изискват допълнителна проверка.
#

DEVICE_PATH := device/motorola/sofiar

# --- Платформа (Qualcomm SM6125 / Snapdragon 665, codename "trinket") ---
TARGET_BOARD_PLATFORM := trinket
TARGET_BOOTLOADER_BOARD_NAME := sofiar
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_VARIANT := kryo
TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := kryo

# --- Kernel source (community-derived, виж reference/device-findings.md) ---
TARGET_KERNEL_SOURCE := kernel/motorola/trinket
TARGET_KERNEL_CONFIG := vendor/sofiar_defconfig
TARGET_KERNEL_ARCH := arm64
TARGET_KERNEL_HEADER_ARCH := arm64
# header_version 2 -> dtb е ОТДЕЛНА секция (не appended към kernel),
# затова Image.gz, не Image.gz-dtb
BOARD_KERNEL_IMAGE_NAME := Image.gz

# --- Boot image header - РЕАЛНИ ДАННИ от recovery.img (header_version 2) ---
BOARD_BOOTIMG_HEADER_VERSION := 2
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_TAGS_OFFSET := 0x00000100
BOARD_RAMDISK_OFFSET := 0x01000000
BOARD_KERNEL_OFFSET := 0x00008000
BOARD_DTB_OFFSET := 0x01F00000
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOTIMG_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --base $(BOARD_KERNEL_BASE)
BOARD_MKBOOTIMG_ARGS += --pagesize $(BOARD_KERNEL_PAGESIZE)
BOARD_MKBOOTIMG_ARGS += --kernel_offset $(BOARD_KERNEL_OFFSET)
BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)
BOARD_MKBOOTIMG_ARGS += --dtb_offset $(BOARD_DTB_OFFSET)
BOARD_INCLUDE_RECOVERY_DTBO := true
BOARD_CUSTOM_BOOTIMG_MK := $(DEVICE_PATH)/bootimg.mk

# --- Партиции - РЕАЛНИ ДАННИ от GPT (виж reference/device-findings.md) ---
BOARD_BOOTIMAGE_PARTITION_SIZE := 67108864        # boot_a/b = 64MB
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 67108864    # recovery_a/b = 64MB
BOARD_DTBOIMG_PARTITION_SIZE := 25165824          # dtbo_a/b = 24MB
BOARD_SUPER_PARTITION_SIZE := 8690401280          # super = 8288MB
BOARD_SUPER_PARTITION_GROUPS := sofiar_dynamic_partitions
BOARD_SOFIAR_DYNAMIC_PARTITIONS_PARTITION_LIST := system vendor product
# TODO: точният размер на dynamic partitions group обикновено е малко
# под пълния super размер (резерв за метаданни) - типично ~1-2% по-малко.
# Ще коригираме, ако build-ът се оплаче за размер при първия опит.
BOARD_SOFIAR_DYNAMIC_PARTITIONS_SIZE := 8656846848

# --- Dynamic partitions / filesystem ---
BOARD_USES_METADATA_PARTITION := true
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true

# --- AVB (Android Verified Boot 2) - vbmeta_a/b потвърдени в GPT-то ---
BOARD_AVB_ENABLE := true
# TODO: това е AOSP test key, ДОБРЕ Е само за `fastboot boot` тестове
# (никога за истински flash) - за реален flash ще трябва истинският
# avb ключ на устройството, или изключване на avb проверката подходящо.
BOARD_AVB_RECOVERY_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_RECOVERY_ALGORITHM := SHA256_RSA4096
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := 0
BOARD_AVB_RECOVERY_ROLLBACK_INDEX_LOCATION := 1

# --- A/B seamless update (recovery_a/b, boot_a/b, dtbo_a/b, vbmeta_a/b потвърдени) ---
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    dtbo \
    recovery \
    system \
    vbmeta \
    vendor

# --- fstab / crypto ---
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery.fstab
TW_INCLUDE_CRYPTO := true
TW_INCLUDE_FBE := true
# ICE (Inline Crypto Engine) - потвърдено от реалния stock fstab
# (fileencryption=ice:aes-256-cts). ИЗВЕСТЕН РИСК - виж
# reference/device-findings.md, не е гарантирано да проработи веднага.
TARGET_USES_QCOM_ICE_FBE := true

# РЕАЛНИ ДАННИ от prop.default (ro.build.version.security_patch / .release)
PLATFORM_SECURITY_PATCH := 2022-02-01
PLATFORM_VERSION := 11

# --- TWRP дисплей - потвърдена резолюция 1080x2300, 399ppi (Motorola official) ---
TW_THEME := portrait_hdpi

# --- Общ (common) tree за sm6125/trinket платформата ---
-include device/motorola/sm6125-common/BoardConfig.mk
