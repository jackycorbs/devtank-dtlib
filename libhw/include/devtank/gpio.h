#ifndef __GPIO__
#define __GPIO__

#include <stdbool.h>

typedef struct gpio_obj_t gpio_obj_t;


extern gpio_obj_t*  gpio_obj_create(const char* path);

extern void         gpio_obj_destroy(gpio_obj_t * obj);


extern bool         gpio_obj_read(gpio_obj_t * obj, bool * value);

extern bool         gpio_obj_write(gpio_obj_t * obj, bool value);


#endif //__GPIO__
