#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>

#include <devtank/log.h>

#include <devtank/gpio.h>


struct gpio_obj_t
{
    char       * path;
};



extern gpio_obj_t*  gpio_obj_create(const char* path)
{
    if (!path)
        return NULL;
    gpio_obj_t* r = malloc(sizeof(gpio_obj_t));
    if (!r)
    {
        error_msg("Failed to allocate gpio_obj");
        return NULL;
    }
    r->path = NULL;
    int e = asprintf(&r->path, "%s/value", path);
    if (e < 0)
    {
        error_msg("Failed to prepare GPIO string : %s", strerror(errno));
        free(r);
        return false;
    }

    return r;
}


extern void         gpio_obj_destroy(gpio_obj_t * obj)
{
    if (!obj)
        return;
    free(obj->path);
    free(obj);
}


extern bool         gpio_obj_read(gpio_obj_t * obj, bool * value)
{
    if (!obj || !value)
        return false;

    char value_str[2];

    int fd = open(obj->path, O_RDONLY);
    if (fd < 0)
    {
        error_msg("Failed to read-open GPIO %s : %s", obj->path,  strerror(errno));
        return false;
    }

    if (read(fd, value_str, sizeof(value_str)) != sizeof(value_str))
    {
        error_msg("Failed to read GPIO %s : %s", obj->path,  strerror(errno));
        close(fd);
        return false;
    }

    close(fd);
    *value = value_str[0] == '1';

    info_msg("GPIO %s read as %c", obj->path, value_str[0]);

    return true;
}


extern bool         gpio_obj_write(gpio_obj_t * obj, bool value)
{
    if (!obj)
        return false;

    int fd = open(obj->path, O_WRONLY);
    if (fd < 0)
    {
        error_msg("Failed to write-open GPIO %s : %s", obj->path,  strerror(errno));
        return false;
    }

    char value_str[2] = { (value)?'1':'0', '\n' };

    if (write(fd, value_str, sizeof(value_str)) != sizeof(value_str))
    {
        error_msg("Failed to write GPIO %s : %s", obj->path,  strerror(errno));
        close(fd);
        return false;
    }
    close(fd);

    info_msg("GPIO %s set as %c", obj->path, value_str[0]);

    return true;
}
