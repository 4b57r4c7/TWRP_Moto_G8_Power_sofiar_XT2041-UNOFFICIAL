# twrp_sofiar.mk - product makefile, избиран от `lunch twrp_sofiar-eng`

$(call inherit-product, $(SRC_TARGET_DIR)/product/embedded.mk)
$(call inherit-product, device/motorola/sofiar/device.mk)

PRODUCT_NAME := twrp_sofiar
PRODUCT_DEVICE := sofiar

# РЕАЛНИ данни от ro.product.system.* в prop.default (stock recovery)
PRODUCT_BRAND := motorola
PRODUCT_MODEL := moto g(8) power
PRODUCT_MANUFACTURER := motorola

PRODUCT_GMS_CLIENTID_BASE := android-motorola
