#include <hardware/hardware.h>
#include <dlfcn.h>
#include <errno.h>
#include <string.h>

/* The acquired MTK module is the old API 0.1 layout: common + two calls.
 * Do not read a modern camera_module_t beyond that prefix. */
struct legacy_camera_info { int facing; int orientation; };
struct legacy_camera_module {
    struct hw_module_t common;
    int (*get_number_of_cameras)(void);
    int (*get_camera_info)(int, struct legacy_camera_info *);
};
static struct legacy_camera_module *original;
static void *original_handle;
static int number_of_cameras(void) {
    return original ? original->get_number_of_cameras() : 0;
}
static int camera_info(int id, struct legacy_camera_info *info) {
    if (!original || !info) return -EINVAL;
    int rc = original->get_camera_info(id,info);
    if (!rc) info->orientation=(info->orientation+180)%360;
    return rc;
}
static int open_device(const struct hw_module_t *module,const char *id,
                       struct hw_device_t **device) {
    (void)module;
    if (!original) return -ENODEV;
    return original->common.methods->open(&original->common,id,device);
}
static struct hw_module_methods_t methods={.open=open_device};
struct legacy_camera_module HAL_MODULE_INFO_SYM;
_Static_assert(sizeof(void *)==4,"This wrapper is ARM32 only");
_Static_assert(sizeof(struct hw_module_t)==128,"Unexpected Android HAL ABI");
__attribute__((constructor)) static void initialize(void) {
    original_handle=dlopen("/system/lib/hw/camera.b8000-original.so",RTLD_NOW|RTLD_LOCAL);
    if (!original_handle) return;
    original=dlsym(original_handle,HAL_MODULE_INFO_SYM_AS_STR);
    if (!original || original->common.module_api_version!=1 ||
        !original->common.id || strcmp(original->common.id,"camera") ||
        !original->get_number_of_cameras || !original->get_camera_info ||
        !original->common.methods || !original->common.methods->open) {
        original=0; return;
    }
    HAL_MODULE_INFO_SYM.common=original->common;
    HAL_MODULE_INFO_SYM.common.methods=&methods;
    HAL_MODULE_INFO_SYM.get_number_of_cameras=number_of_cameras;
    HAL_MODULE_INFO_SYM.get_camera_info=camera_info;
}
