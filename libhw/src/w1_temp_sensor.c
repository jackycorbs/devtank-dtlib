#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#include <devtank/log.h>

#include <devtank/w1_temp_sensor.h>



struct w1_temp_sense_t
{
    FILE * file;
    char   path[1];
    volatile double last_value;
};


w1_temp_sense_t* w1_temp_sense_create(const char* device_file)
{
    if (!device_file)
        return NULL;

    int len =  strlen(device_file);

    w1_temp_sense_t * r = malloc(sizeof(w1_temp_sense_t) + len);

    if (!r)
    {
        error_msg("Failed to allocate w1_temp_sense for %s", device_file);
        return NULL;
    }

    r->file =  fopen(device_file, "r");
    if (!r->file)
    {
        free(r);
        error_msg("Failed to open temperature sensor: %s : %s", device_file, strerror(errno));
        return NULL;
    }

    setbuf(r->file, NULL);
    memcpy(r->path, device_file, len+1);
    r->last_value = 0;

    info_msg("Open temperature sensor: %s", device_file);

    return r;
}


bool             w1_temp_sense_read(w1_temp_sense_t* sensor, double* temp)
{
    if (!sensor || !temp)
        return false;

    char buffer[2024];
    char* line = buffer;
    ssize_t line_len;
    size_t line_max_len = 1024;
    bool crc_line = true;

    while ((line_len = getline(&line, &line_max_len, sensor->file)) >= 0)
    {
        if (line_len > 0)
            line[line_len] = 0;

        if (crc_line)
        {
            char* pos = strstr(line, "crc=");
            if (pos)
            {
                if (strstr(pos, "YES"))
                   crc_line = false;
            }
        }
        else
        {
            char* pos = strstr(line, "t=");
            if (pos)
            {
                pos += 2;
                *temp = strtoul(pos, NULL, 10) / 1000.0;
                sensor->last_value = *temp;

                info_msg("Read temperature sensor: %s : %G°", sensor->path, *temp);
                fseek(sensor->file, 0, SEEK_SET);
                return true;
            }
        }
    }

    warning_msg("Read temperature sensor: %s failed.", sensor->path);
    return false;
}


bool             w1_temp_sense_read_cached(w1_temp_sense_t* sensor, double* temp)
{
    if (!sensor || !temp)
        return false;

    *temp = sensor->last_value;
    return true;
}


void             w1_temp_sense_destroy(w1_temp_sense_t* sensor)
{
    if (!sensor)
        return;

    fclose(sensor->file);
    free(sensor);
}
