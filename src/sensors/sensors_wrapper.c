#include <hardware/sensors.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

/* B8000's panel is mounted 180 degrees from the legacy sensor frame. */
static struct sensors_module_t *original_module;
static void *original_handle;
struct wrapper { struct sensors_poll_device_t api; struct sensors_poll_device_t *real; };
static struct wrapper *wrap(struct sensors_poll_device_t *d) { return (struct wrapper *)d; }
static int close_device(struct hw_device_t *d) {
    struct wrapper *w=(struct wrapper *)d;
    int rc=w->real->common.close(&w->real->common); free(w); return rc;
}
static int activate(struct sensors_poll_device_t *d,int handle,int enabled) {
    return wrap(d)->real->activate(wrap(d)->real,handle,enabled);
}
static int delay(struct sensors_poll_device_t *d,int handle,int64_t ns) {
    return wrap(d)->real->setDelay(wrap(d)->real,handle,ns);
}
static int poll_events(struct sensors_poll_device_t *d,sensors_event_t *events,int count) {
    int n=wrap(d)->real->poll(wrap(d)->real,events,count);
    for(int i=0;i<n;i++) {
        sensors_event_t *e=&events[i];
        switch(e->type) {
        case SENSOR_TYPE_ACCELEROMETER:
        case SENSOR_TYPE_MAGNETIC_FIELD:
            e->data[0]=-e->data[0]; e->data[1]=-e->data[1]; break;
        case SENSOR_TYPE_ORIENTATION:
            e->data[0]+=180.0f;
            if(e->data[0]>=360.0f) e->data[0]-=360.0f;
            e->data[1]=-e->data[1]; e->data[2]=-e->data[2]; break;
        }
    }
    return n;
}
static int open_device(const struct hw_module_t *module,const char *id,struct hw_device_t **out) {
    (void)module;
    if(!original_module) return -ENODEV;
    struct sensors_poll_device_t *real=NULL;
    int rc=original_module->common.methods->open(&original_module->common,id,(struct hw_device_t **)&real);
    if(rc) return rc;
    /* The acquired Lenovo driver is API 0. Never misrepresent a newer ABI. */
    if(real->common.version!=0 && real->common.version!=1 &&
       real->common.version!=SENSORS_DEVICE_API_VERSION_0_1) {
        real->common.close(&real->common); return -EINVAL;
    }
    struct wrapper *w=calloc(1,sizeof(*w));
    if(!w) { real->common.close(&real->common); return -ENOMEM; }
    w->real=real; w->api=*real; w->api.common.close=close_device;
    w->api.activate=activate; w->api.setDelay=delay; w->api.poll=poll_events;
    *out=&w->api.common; return 0;
}
static int sensor_list(struct sensors_module_t *module,struct sensor_t const **list) {
    (void)module;
    return original_module ? original_module->get_sensors_list(original_module,list) : -ENODEV;
}
static struct hw_module_methods_t methods={.open=open_device};
struct sensors_module_t HAL_MODULE_INFO_SYM;
__attribute__((constructor)) static void initialize(void) {
    original_handle=dlopen("/system/lib/hw/sensors.b8000-stock.so",RTLD_NOW|RTLD_LOCAL);
    if(!original_handle) return;
    original_module=dlsym(original_handle,HAL_MODULE_INFO_SYM_AS_STR);
    if(!original_module) return;
    HAL_MODULE_INFO_SYM.common=original_module->common;
    HAL_MODULE_INFO_SYM.common.methods=&methods;
    HAL_MODULE_INFO_SYM.get_sensors_list=sensor_list;
}
