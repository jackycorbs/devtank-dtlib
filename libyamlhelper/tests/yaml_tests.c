/*
 * Copyright (c) 2018 DevTank Ltd
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include "devtank/helpers/yaml_helper.h"
#include "tests.h"


bool root_entry_check_cb(dt_yaml_loader_t* loader UNUSED, const char* key, const char* value)
{
    info_msg("Map child '%s' with value '%s'", key, value);

    if (!strcmp(key, "my_int"))
    {
        if (!strcmp(value, "44"))
            return true;
        return false;
    }
    if (!strcmp(key, "my_str"))
    {
        if (!strcmp(value, "hello"))
            return true;
        return false;
    }
    if (!strcmp(key, "my_list"))
    {
        unsigned * index = (unsigned*)dt_yaml_loader_get_userdata(loader);
        unsigned child_int = strtoul(value, NULL, 10);

        info_msg("Array %u with int %u", *index, child_int);

        if (child_int != ((*index) + 2))
            return false;

        (*index) += 1;

        return true;
    }
    return false;
}

bool root_map_check_cb(dt_yaml_loader_t* loader, const char* key UNUSED)
{
    unsigned array_index = 0;

    dt_yaml_loader_set_userdata(loader, &array_index);

    return dt_yaml_loader_do(loader, NULL, NULL, root_entry_check_cb);
}


int main(int argc UNUSED, char* argv[] UNUSED)
{
    if (getenv("DEBUG"))
    {
        enable_info_msgs(true);
        info_msg("Debug enabled");
    }

    bool r = dt_yaml_save("/tmp/test.yaml", &(dt_yaml_element_t){
        type: DT_YAML_MAP, map_entries: (dt_yaml_map_entry_t[]){
            { key: "my_int", value: {type: DT_YAML_INTEGER, i_value: 44} },
            { key: "my_str", value: {type: DT_YAML_STRING, s_value: "hello"} },
            { key: "my_list", value: {type: DT_YAML_ARRAY, array_entries:
                (dt_yaml_element_t[]){
                    { type: DT_YAML_INTEGER, i_value: 2 },
                    { type: DT_YAML_INTEGER, i_value: 3 },
                    { type: DT_YAML_INTEGER, i_value: 4 },
                    { type: DT_YAML_NONE },
                    } }},
            { NULL }
        }});
    expect_success(r, "Save YAML Test");

    dt_yaml_loader_t * loader = dt_yaml_loader_open_file("/tmp/test.yaml", NULL);

    if (!loader)
        return EXIT_FAILURE;

    r = dt_yaml_loader_do(loader, root_map_check_cb, NULL, NULL);
    dt_yaml_loader_destroy(loader);

    expect_success(r, "Load YAML Test");

    if (!r)
        return EXIT_FAILURE;

    return EXIT_SUCCESS;
}
