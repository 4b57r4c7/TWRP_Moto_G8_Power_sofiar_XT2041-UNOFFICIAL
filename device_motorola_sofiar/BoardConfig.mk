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

# --- Kernel: PREBUILT от stock recovery.img (RPES31.Q4U-47-35-12) ---
# Компилираният от source kernel (trinket-perf_defconfig) НЕ включва
# sofiar-специфичните драйвери (напр. CONFIG_BACKLIGHT_AW99703 от
# ext_config/moto-trinket-sofiar.config) - вероятен черен екран. Stock
# kernel-ът е точно този, който телефонът реално bootва, и съвпада по
# версия с vendor модулите (тъч драйверите) на телефона.
# Файловете се извличат с tools/extract_prebuilts.py.
TARGET_KERNEL_ARCH := arm64
TARGET_KERNEL_HEADER_ARCH := arm64
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/kernel
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR := $(DEVICE_PATH)/prebuilt/dtb
BOARD_PREBUILT_RECOVERY_DTBOIMAGE := $(DEVICE_PATH)/prebuilt/recovery_dtbo

# Stock cmdline (РЕАЛНИ ДАННИ от recovery.img header, без buildvariant=user,
# което build-ът добавя сам) + selinux permissive само за TWRP
BOARD_KERNEL_CMDLINE := console=ttyMSM0,115200,n8 androidboot.hardware=qcom androidboot.console=ttyMSM0 androidboot.memcg=1 lpm_levels.sleep_disabled=1 video=vfb:640x400,bpp=32,memsize=3072000 msm_rtb.filter=0x237 service_locator.enable=1 swiotlb=1 earlycon=msm_geni_serial,0x4a90000 loop.max_part=7 cgroup.memory=nokmem,nosocket androidboot.usbcontroller=4e00000.dwc3 printk.devkmsg=on androidboot.hab.csv=19 androidboot.hab.product=sofiar androidboot.hab.cid=50 firmware_class.path=/vendor/firmware_mnt/image
BOARD_KERNEL_CMDLINE += androidboot.selinux=permissive

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

# vendor/product са отделни логически дялове в super - иначе build-ът
# прави root/vendor и root/product symlink-ове към /system/..., които
# се сблъскват с файловете от common.mk (rsync "could not make way for new symlink")
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_PRODUCT := product

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
# КРИПТИРАНЕТО Е ВРЕМЕННО ИЗКЛЮЧЕНО. Първият fastboot boot тест показа
# (last_kmsg), че TWRP виси преди UI-а в опит да декриптира /data:
# чака keymaster HAL, който не тръгва в recovery. Първо искаме работещ
# екран/тъч/adb, декриптирането идва отделно след това.
# TW_INCLUDE_CRYPTO := true
# TW_INCLUDE_FBE := true
# TARGET_USES_QCOM_ICE_FBE := true

# РЕАЛНИ ДАННИ от prop.default (ro.build.version.security_patch / .release)
PLATFORM_SECURITY_PATCH := 2022-02-01
PLATFORM_VERSION := 11

# --- TWRP дисплей - потвърдена резолюция 1080x2300, 399ppi (Motorola official) ---
TW_THEME := portrait_hdpi

# Дисплей/вход/USB - взети от sm6125-common/BoardConfigCommon.mk (същата
# trinket Moto платформа). Нашият -include на common по-долу сочи към
# несъществуващ BoardConfig.mk, затова ги слагаме тук изрично.
TARGET_RECOVERY_PIXEL_FORMAT := "RGBX_8888"
TW_SCREEN_BLANK_ON_BOOT := true
TW_INPUT_BLACKLIST := "hbtp_vm"
TARGET_RECOVERY_QCOM_RTC_FIX := true
# Ползва Moto-специфичния init.recovery.usb.rc от common tree-то вместо
# стандартния TWRP (иначе rsync-ът го презаписва с TWRP default-а)
TW_EXCLUDE_DEFAULT_USB_INIT := true
TW_EXCLUDE_TWRPAPP := true
TW_USE_TOOLBOX := true
# logcat в recovery - за диагностика, докато довършваме
TWRP_INCLUDE_LOGCAT := true
TARGET_USES_LOGD := true

# --- Общ (common) tree за sm6125/trinket платформата ---
# common.mk копира десетки ELF binary/.so файлове през PRODUCT_COPY_FILES
# (стар, но легитимен TWRP device tree подход) - по-новата build
# система изисква такива да са декларирани като cc_prebuilt_* Soong
# модули и отхвърля raw copy с "found ELF prebuilt in PRODUCT_COPY_FILES".
# Този флаг изключва проверката за целия build (стандартен AOSP escape
# hatch точно за такъв случай), вместо да пренаписваме всеки prebuilt.
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true

-include device/motorola/sm6125-common/BoardConfig.mk
