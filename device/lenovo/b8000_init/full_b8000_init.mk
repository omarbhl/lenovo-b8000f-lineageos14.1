$(call inherit-product, $(SRC_TARGET_DIR)/product/embedded.mk)
PRODUCT_NAME := full_b8000_init
PRODUCT_DEVICE := b8000_init
PRODUCT_BRAND := Lenovo
PRODUCT_MODEL := B8000-F init build
PRODUCT_MANUFACTURER := Lenovo
PRODUCT_PACKAGES += init
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += ro.zygote=zygote32
