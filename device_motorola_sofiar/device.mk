# device.mk - Motorola Moto G8 Power (sofiar)

LOCAL_PATH := device/motorola/sofiar

# ПРОВЕРИ: точното име/път на common product makefile-а в
# sm6125-common tree-то - варира между форковете (напр.
# common.mk / device-common.mk / device_common.mk). Ако build-ът
# гръмне тук с "cannot find" - виж какво реално има в
# device/motorola/sm6125-common/ след repo sync и коригирай.
$(call inherit-product, device/motorola/sm6125-common/common.mk)

PRODUCT_DEVICE := sofiar

# Архитектура (arm64, потвърдена от kernel header анализа по-рано)
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic

# fstab-ът вече се копира автоматично чрез TARGET_RECOVERY_FSTAB
# в BoardConfig.mk - не е нужен допълнителен PRODUCT_COPY_FILES ред.
