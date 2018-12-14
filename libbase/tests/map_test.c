/*
 * Copyright (c) 2016 DevTank Ltd
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
#include <stdlib.h>
#include <string.h>
#include "tests.h"
#include "devtank/map.h"

static const void * _expected_item = NULL;

typedef struct
{
    const char* key;
    const char* info;
} test_node_t;



uint8_t     test_key_hash(const void* key, void *unused)
{
    int hash = 7;
    const char* skey = (const char*)key;
    for (int i = 0; i < strlen(skey); i++)
        hash = hash*31 + skey[i];
    return (uint8_t)(hash & 0xFF);
}


bool        test_key_match(const void* a, const void* b, void *unused)
{
    const char* sa = (const char*)a;
    const char* sb = (const char*)b;

    return (strcmp(sa, sb) == 0);
}


const void* test_item_key(const void* item, void *unused)
{
    test_node_t* node = (test_node_t*)item;
    return node->key;
}


void        test_item_delete(void* item, void* unused)
{
    expect_success (_expected_item == item, "Expect item deleted.");
}



int main(int argc, char* argv[])
{
    dt_map_t map;

    dt_map_init(&map, test_key_hash, test_key_match, test_item_key, test_item_delete, NULL);

    test_node_t a = {"a", "first"};
    test_node_t b = {"b", "second"};
    test_node_t c = {"c", "third"};

    expect_success( dt_map_add(&map, &a) &&
                    dt_map_add(&map, &b) &&
                    dt_map_add(&map, &c), "Adding A,B,C");

    test_node_t * a2 = dt_map_find(&map, "a");
    test_node_t * b2 = dt_map_find(&map, "b");
    test_node_t * c2 = dt_map_find(&map, "c");

    expect_success(a2 && !strcmp(a2->key, a.key) , "Find A");
    expect_success(a2 && !strcmp(b2->key, b.key) , "Find B");
    expect_success(a2 && !strcmp(c2->key, c.key) , "Find C");

    _expected_item = &a;
    dt_map_remove(&map, "a");
    a2 = dt_map_find(&map, "a");
    expect_success(!a2 , "Removed A");

    _expected_item = &b;
    dt_map_remove(&map, "b");
    b2 = dt_map_find(&map, "b");
    expect_success(!a2 , "Removed B");

    _expected_item = &c;
    dt_map_remove(&map, "c");
    c2 = dt_map_find(&map, "c");
    expect_success(!a2 , "Removed C");

    dt_map_clear(&map);

    return 0;
}
