#ifndef __W1_TEMP_SENSOR__
#define __W1_TEMP_SENSOR__

#include <stdbool.h>

typedef struct w1_temp_sense_t w1_temp_sense_t;

extern w1_temp_sense_t* w1_temp_sense_create(const char* device_file);

extern bool             w1_temp_sense_read(w1_temp_sense_t* sensor, double* temp);

extern bool             w1_temp_sense_read_cached(w1_temp_sense_t* sensor, double* temp);

extern void             w1_temp_sense_destroy(w1_temp_sense_t* sensor);

#endif //__W1_TEMP_SENSOR__
